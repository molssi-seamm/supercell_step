.. _user-guide:

**********
User Guide
**********
The Supercell step builds an ``na`` x ``nb`` x ``nc`` supercell of the current periodic
system: the cell is multiplied along each axis and the atoms and their bonds are copied
into each new cell. A structure with symmetry is first expanded to P1.

The supercell can overwrite the current configuration (the default), be added as a new
configuration of the current system, or be put in a new system, as in SEAMM's other
steps that make structures; the original is left unchanged in the latter two cases. By
default the names are kept -- a new system or configuration takes the current one's
name -- or the configuration can be named after the supercell, e.g. ``2 x 2 x 1
supercell``; the system's name is asked for only when a new system is made.

..
   The following sections cover accessing and controlling this functionality.

   .. toctree::
      :maxdepth: 2
      :titlesonly:

Index
=====

* :ref:`genindex`
