=======
History
=======
2026.10.6 -- SEAMM's standard choices for the supercell; bugfixes for bonded systems
    * The supercell can overwrite the current configuration (the default, as before),
      go in a new configuration or in a new system, with SEAMM's standard choices and
      names; the original is left as it was in the latter two. Names are kept by
      default, or the configuration can be named after the supercell, e.g. "2 x 2 x 1
      supercell"; the system name is asked for only when a new system is made.
    * Bugfix: a supercell of a structure with bonds failed (the atoms' row positions
      were taken for their ids), as did one three or more cells long in any direction
      (the bonds of each copy were mapped from the previous copy's).
    * Builds again from its source distribution; requires seamm 2026.10.3 and
      molsystem 2026.10.6, which lowers the symmetry of structures with bonds.

2025.6.25.1 -- Bugfix: fixed crash caused by gradients.
    * The addition of the gradients to the atom data caused a crash when expanding the
      cell. Since it doesn't obviously make sense to expand the gradients, they are
      ignored when building a supercell.

2025.6.25 -- Bugfix: avoid lowering symmetry for P1 systems.

2023.11.5 -- Updated to handle symmetry in systems

2021.2.12 --
    * Updated the README file to give a better description.
    * Updated the short description in setup.py to work with the new installer.
    * Added keywords for better searchability.

2021.2.4 --
    * Updated for compatibility with the new system classes in MolSystem
      2021.2.2 release.

2020.12.5 -- 
    * Added support for non-orthorhombic cells.
    * Updated to be compatible with the new system classes in MolSystem.
    * Internal: switching CI from TravisCI to GitHub Actions, and in the
      process moving documentation from ReadTheDocs to GitHub Pages where
      it is consolidated with the main SEAMM documentation.

0.9.1 -- 20 June 2020
    * Bugfix: Was not properly copying charges to the new system.

0.9 -- 18 June 2020
    * First release on PyPI.
    * Working but only for orthorhombic cells
