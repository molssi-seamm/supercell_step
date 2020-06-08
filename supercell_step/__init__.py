# -*- coding: utf-8 -*-

"""
supercell_step
A step for building supercells of periodic systems.
"""

# Bring up the classes so that they appear to be directly in
# the supercell_step package.

from supercell_step.supercell import Supercell  # noqa: F401, E501
from supercell_step.supercell_parameters import SupercellParameters  # noqa: F401, E501
from supercell_step.supercell_step import SupercellStep  # noqa: F401, E501
from supercell_step.tk_supercell import TkSupercell  # noqa: F401, E501

# Handle versioneer
from ._version import get_versions
__author__ = """Paul Saxe"""
__email__ = 'psaxe@molssi.org'
versions = get_versions()
__version__ = versions['version']
__git_revision__ = versions['full-revisionid']
del get_versions, versions
