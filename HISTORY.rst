=======
History
=======
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
