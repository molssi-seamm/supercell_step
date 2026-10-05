# -*- coding: utf-8 -*-

"""
supercell_step
A step for building supercells of periodic systems.
"""

# Bring up the classes so that they appear to be directly in
# the supercell_step package.

import copy

import seamm


from supercell_step.supercell import Supercell  # noqa: F401, E501
from supercell_step.supercell_parameters import SupercellParameters  # noqa: F401, E501
from supercell_step.supercell_step import SupercellStep  # noqa: F401, E501
from supercell_step.tk_supercell import TkSupercell  # noqa: F401, E501

# Handle versioneer
from ._version import get_versions

# How the supercell is handled: SEAMM's standard structure handling, less the
# choices that make no sense here -- one structure is made, and discarding it
# would leave nothing -- defaulting, as before, to overwriting the current
# configuration.
structure_handling_parameters = copy.deepcopy(
    seamm.standard_parameters.structure_handling_parameters
)
del structure_handling_parameters["subsequent structure handling"]
_handling = structure_handling_parameters["structure handling"]
_handling["default"] = "Overwrite the current configuration"
_handling["enumeration"] = tuple(
    e for e in _handling["enumeration"] if e != "Discard the structure"
)
_handling["description"] = "Supercell:"
structure_handling_parameters["system name"]["default"] = "keep current name"
_names = structure_handling_parameters["configuration name"]
#: Names the configuration after the supercell, e.g. '2 x 2 x 1 supercell'
SUPERCELL_NAME = "<na> x <nb> x <nc> supercell"
_names["default"] = "keep current name"
_names["enumeration"] = ("keep current name", SUPERCELL_NAME) + tuple(
    e for e in _names["enumeration"] if e != "keep current name"
)
del _handling, _names

__author__ = """Paul Saxe"""
__email__ = "psaxe@molssi.org"
versions = get_versions()
__version__ = versions["version"]
__git_revision__ = versions["full-revisionid"]
del get_versions, versions
