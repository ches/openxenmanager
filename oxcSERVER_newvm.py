# -----------------------------------------------------------------------
# OpenXenManager
#
# Copyright (C) 2009 Alberto Gonzalez Rodriguez alberto@pesadilla.org
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------
import xmlrpclib, urllib
import asyncore, socket
import select
import gtk
from os import chdir
import platform
import sys, shutil
import datetime
from threading import Thread
from configobj import ConfigObj
import xml.dom.minidom 
from operator import itemgetter
import pdb
import rrdinfo
import time
import gobject
from messages import messages, messages_header

class oxcSERVERnewvm:
    def get_path_available_host(self):
        path = 0
        i = 0
        for host in self.all_hosts.keys():
            if self.all_hosts[host]['enabled']:
                path = i 
            i = i + 1
        return path

    def first_network(self):
        for network in self.all_network:
            return self.all_network[network]['name_label'].replace('Pool-wide network associated with eth','Network ')
    def first_network_ref(self):
        for network in self.all_network:
            return network
    def fill_listnewvmstorage(self, list, vm, host, ref):
        list.clear()
        if "disks" in self.all_vms[vm]['other_config']:
            dom = xml.dom.minidom.parseString(self.all_vms[vm]['other_config']['disks'])
            nodes = dom.getElementsByTagName("disk")
            for node in nodes: 
               if self.default_sr == "OpaqueRef:NULL" or self.default_sr not in self.all_storage:
                    self.default_sr = self.all_storage.keys()[0]
               list.append(["%0.2f" % (float(node.attributes.getNamedItem("size").value)/1024/1024/1024), 
                        self.all_storage[self.default_sr]['name_label'] + " on " + 
                        self.all_hosts[host]['name_label'], 
                        str(self.all_storage[self.default_sr]['shared']),ref])
        else:
            for vbd in self.all_vbd:
                    if self.all_vbd[vbd]['VM'] == vm:
                        if self.all_vbd[vbd]["type"] == "Disk":
                            vdi =  self.all_vbd[vbd]["VDI"]
                            list.append(["%0.2f" % (float(self.all_vdi[vdi]["virtual_size"])/1024/1024/1024),
                                     self.all_storage[self.default_sr]['name_label'] + " on " +
                                     self.all_hosts[host]['name_label'],
                                      str(self.all_storage[self.default_sr]['shared']),ref])


    def fill_listnewvmdisk(self, list, host):
        list.clear()
        i = 0
        default_sr = 0
        for sr in self.all_storage.keys():
            storage = self.all_storage[sr]
            if storage['type'] != "iso" and storage['type'] != "udev":
                if self.default_sr == sr:
                    default_sr = i
            try:
                list.append([storage['name_label'],
                    storage['name_description'],
                    self.convert_bytes(storage['physical_size']),
                    self.convert_bytes(int(storage['physical_size'])-int(storage['virtual_allocation'])), sr])
            except:
                    pass
            i = i + 1
        return default_sr 

    def create_newvm(self, data):
        res = self.connection.VM.clone(self.session_uuid, data['ref'], data['name'])
        if not "Value" in res:
            self.wine.show_error_dlg(str(res["ErrorDescription"]))
            return
        vm_uuid = res['Value']
        if data["startvm"]:
            self.autostart[vm_uuid] = data['host']
        self.connection.VM.set_name_description(self.session_uuid, vm_uuid, data['description'])
        other_config = self.all_vms[data['ref']]['other_config'] 
        other_config["default_template"] = "false"
        selection = self.wine.builder.get_object("treenewvmstorage").get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.select_all()
        model, selected = selection.get_selected_rows()
        iters = [model.get_iter(path) for path in selected]
        i = 0
        disk = "<provision>"
        for iter_ref in iters:
            size = int(float(self.wine.builder.get_object("listnewvmstorage").get_value(iter_ref, 0))*1024*1024*1024)
            sr = self.all_storage[self.wine.builder.get_object("listnewvmstorage").get_value(iter_ref, 3)]["uuid"]
            if "postinstall" not in other_config and data["location"] != "radiobutton1":
                disk += '<disk device="%d" size="%d" sr="%s" bootable="false" type="system" ionice="0" readonly="False" />' % (i, size, sr)
            else:    
                if i == 0:
                    disk += '<disk device="%d" size="%d" sr="%s" bootable="true" type="system" ionice="0" readonly="False" />' % (i, size, sr)
                else:
                    disk += '<disk device="%d" size="%d" sr="%s" bootable="false" type="system" ionice="0" readonly="False" />' % (i, size, sr)
            i = i + 1
        disk += "</provision>"
        setdisks = True
        for vbd in self.all_vbd:
            if self.all_vbd[vbd]['VM'] == data["ref"]:
                if self.all_vbd[vbd]["type"] == "Disk":
                    setdisks = False

        if setdisks:
            other_config['disks'] = disk
        selection.unselect_all()
        self.connection.VM.set_affinity(self.session_uuid, data['host'])
        if "postinstall" not in other_config:
            if data["location"] == "radiobutton1":
                other_config["install-repository"] = data['location_url']
            else:
                other_config["install-repository"] = "cdrom"
        from uuid import uuid1 as uuid
        other_config["mac_seed"] = str(uuid())
        self.connection.VM.set_other_config(self.session_uuid, vm_uuid, other_config)
        ref = self.connection.VM.provision( 
                self.session_uuid, vm_uuid) 

        
        self.track_tasks[ref['Value']] = vm_uuid
        vif_cfg = {
            'uuid': '',
            'allowed_operations': [],
            'current_operations': {},
            'device': '0',
            'network': '',
            'VM': '',
            'MAC': '',
            'MTU': '0',
            "other_config":         {},
            'currently_attached': False,
            'status_code': "0",
            'status_detail': "",
            "runtime_properties": {},
            "qos_algorithm_type":   "",
            "qos_algorithm_params": {},
            "metrics": "",
            'MAC_autogenerated': False 
        }


        vbd_cfg = {
            'VM': vm_uuid,
            'VDI': data['vdi'],
            'userdevice': str(len(iters)+1),
            'bootable': True,
            'mode': "RO",
            'type': "CD",
            'unplugabble': "0",
            'storage_lock': "0",
            'empty': False,
            'currently_attached': "0",
            'status_code': "0",
            'other_config': {},
            'qos_algorithm_type': "",
            'qos_algorithm_params': {},
        }
        if data['vdi']:
            res = self.connection.VBD.create(self.session_uuid, vbd_cfg)
            self.connection.VBD.insert(self.session_uuid, res['Value'], data['vdi'])

        selection = self.wine.builder.get_object("treenewvmnetwork").get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.select_all()
        model, selected = selection.get_selected_rows()
        iters = [model.get_iter(path) for path in selected]
        i = 0
        memory = int(data['memorymb'])
        res = self.connection.VM.set_memory_limits(self.session_uuid, ref, str(16777216),  str(int(memory*1024*1024)), str(int(memory*1024*1024)), str(int(memory*1024*1024)))
        if "Value" in res:
          self.track_tasks[res['Value']] = ref
        else:
           if res["ErrorDescription"][0] == "MESSAGE_METHOD_UNKNOWN":
                self.connection.VM.set_memory_static_min(self.session_uuid, vm_uuid, str(memory*1024*1024))
                self.connection.VM.set_memory_dynamic_min(self.session_uuid, vm_uuid, str(memory*1024*1024))
                self.connection.VM.set_memory_static_max(self.session_uuid, vm_uuid, str(memory*1024*1024))
                self.connection.VM.set_memory_dynamic_max(self.session_uuid, vm_uuid, str(memory*1024*1024))
                self.connection.VM.set_VCPUs_max (self.session_uuid, vm_uuid, str(int(data['numberofvcpus'])))
                self.connection.VM.set_VCPUs_at_startup(self.session_uuid, vm_uuid, str(int(data['numberofvcpus'])))
                self.connection.VM.set_PV_args(self.session_uuid, vm_uuid, data['entrybootparameters'])

        for iter_ref in iters:
            vif_cfg['device'] = str(i)
            vif_cfg['network'] = self.wine.builder.get_object("listnewvmnetworks").get_value(iter_ref, 3)
            vif_cfg['VM'] = vm_uuid
            self.connection.VIF.create(self.session_uuid, vif_cfg)
            i = i +1 

