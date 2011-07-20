Note
----

This is a git-svn clone of the project's SVN repo on SourceForge. The [project's
wiki][oxm-trac] states that it is unmaintained as of June 2011.

Given the uncertain future, I've mirrored it on GitHub in case the SVN repo
is taken offline, and/or in case the eased collaboration of git and GitHub can
help potential contributors jump in more easily to keep it alive.

However, for the time being PLEASE base any work off of the 'git' branch, as
I will locally maintain the SVN linkage on master in case someone takes over
the project and wishes to stay with the existing SourceForge/Trac 
infrastructure. In that case, if anyone has sent me pull requests, I'll merge
and 'dcommit' on master and work with the new maintainers to get SVN access or
send patches.

The original README content follows at bottom.

[oxm-trac]: http://sourceforge.net/apps/trac/openxenmanager/wiki

### A note for OS X users who may wish to contribute ###

Getting PyGTK's dependencies built is... unpleasant. I've documented a
[procedure I used successfully][pygtk-osx] with Homebrew and Python virtualenv.

[pygtk-osx]: https://gist.github.com/1094799

-----

    You need pygtk
    You need ubuntu jaunty or debian unstable (glade 3.6 and libgtk 2.16)
    You need python-gtk-vnc

    Install rrdtool for graphs

    To launch openxenmanager:

    python window.py

    Please visit #openxenmanager in irc.freenode.net to talk about alpha version
    Or send me mail to alberto@pesadilla.org with "openxenmanager: " subject

