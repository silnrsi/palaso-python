Palaso-Python
-------------
This contains python scripts, modules, and packages created by SIL at the Payap
Linguistic Institute Computing Unit. These are used by - and made available for
future use - by Payap language software developed at the Computing Unit.

This includes modules for:

* Import, export & manipulation of collation data (palaso.collation)
* Data generation from regexps (palaso.reggen)
* A Python interface to SIL's TECkit encoding conversion library.
* SFM & USFM parser

This is a standard python setuptools project, with debian packaging in the
``debian/master`` branch.

Several packages have been promoted to the own external repositories these 
included:

* The Smith font & keyboard build system: https://github.com/silnrsi/smith
* palaso.sldr & scripts have moved to: https://github.com/silnrsi/sldrtools

This package has several extra dependency sets for enabling less frequently
used modules or features:
:debian: Enable ``palaso.debian`` and it tools.
:fontforge: Enable the deprecated ``palaso.font.fontforge`` module and
            several tools that depend on it.
:gtk: Enables the ``palaso.gtk`` package and tools.
:kmn: ``palaso.kmn`` dependencies, particularly the ``keyman2ldml`` tool.
:sklearn: Enables ``grkern2fea`` tool.
:sldr: Enable the deprecated ``palaso.sldr`` package which re-exports the
       ``sldrtools`` package.
:vcs: Enables the vcsaggro tool.

Some tools and modules require packages from the OS package manager, that
have no pypi distributed versions.  
You will need these packages installed if you wish to run the
following:
:gir1.2-webkit2-4.0: ``vcsaggro``
:gir1.2-gtk-3.0: ``getclip``, ``gladerunner``
:fontforge: ``ap2sfd``, ``ffbuilder``, ``ffpointreplace``, ``ufo2sfd`` and
            the ``palaso.font.fontforge`` module.
