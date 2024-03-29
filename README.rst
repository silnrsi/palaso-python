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
