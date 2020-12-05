# -*- coding: utf-8 -*-

"""Non-graphical part of the Supercell step in a SEAMM flowchart
"""

import logging
import seamm
from seamm import data  # noqa: F401
from seamm_util import ureg, Q_  # noqa: F401
import seamm_util.printing as printing
from seamm_util.printing import FormattedText as __
import supercell_step

# In addition to the normal logger, two logger-like printing facilities are
# defined: 'job' and 'printer'. 'job' send output to the main job.out file for
# the job, and should be used very sparingly, typically to echo what this step
# will do in the initial summary of the job.
#
# 'printer' sends output to the file 'step.out' in this steps working
# directory, and is used for all normal output from this step.

logger = logging.getLogger(__name__)
job = printing.getPrinter()
printer = printing.getPrinter('Supercell')


class Supercell(seamm.Node):
    """
    The non-graphical part of a Supercell step in a flowchart.

    Attributes
    ----------
    options : tuple
        It contains a two item tuple containing the populated namespace and the
        list of remaining argument strings.

    subflowchart : seamm.Flowchart
        A SEAMM Flowchart object that represents a subflowchart, if needed.

    parameters : SupercellParameters
        The control parameters for Supercell.

    See Also
    --------
    TkSupercell,
    Supercell, SupercellParameters
    """

    def __init__(self, flowchart=None, title='Supercell', extension=None):
        """A step for Supercell in a SEAMM flowchart.

        You may wish to change the title above, which is the string displayed
        in the box representing the step in the flowchart.

        Parameters
        ----------
            flowchart: seamm.Flowchart
                The non-graphical flowchart that contains this step.

            title: str
                The name displayed in the flowchart.
            extension: None
                Not yet implemented
        """
        super().__init__(
            flowchart=flowchart,
            title='Supercell',
            extension=extension,
            logger=logger
        )

        self.parameters = supercell_step.SupercellParameters()

    @property
    def version(self):
        """The semantic version of this module.
        """
        return supercell_step.__version__

    @property
    def git_revision(self):
        """The git version of this module.
        """
        return supercell_step.__git_revision__

    def description_text(self, P=None):
        """Create the text description of what this step will do.
        The dictionary of control values is passed in as P so that
        the code can test values, etc.

        Parameters
        ----------
            P: dict
                An optional dictionary of the current values of the control
                parameters.
        Returns
        -------
            description : str
                A description of the current step.
        """

        if not P:
            P = self.parameters.values_to_dict()

        text = ('Create a {na} x {nb} x {nc} supercell from the current cell')

        return self.header + '\n' + __(text, **P, indent=4 * ' ').__str__()

    def run(self):
        """Create the supercell.

        Returns
        -------
        next_node : seamm.Node
            The next node object in the flowchart.

        """

        next_node = super().run(printer)
        # Get the values of the parameters, dereferencing any variables
        P = self.parameters.current_values_to_dict(
            context=seamm.flowchart_variables._data
        )

        # Print what we are doing
        printer.important(__(self.description_text(P), indent=self.indent))

        # Get the current system
        if data.structure is None:
            self.logger.error('Supercell: there is no system!')
            raise RuntimeError('Supercell: there is no system to solvate!')

        system = data.structure
        atoms = system['atoms']
        n_atoms = len(atoms['elements'])
        bonds = system['bonds']

        a, b, c, alpha, beta, gamma = system['cell']
        if alpha != 90 or beta != 90 or gamma != 90:
            raise NotImplementedError(
                'Supercell cannot handle non-orthorhombic cells yet'
            )
        lx = int(a * 1000) / 1000
        ly = int(b * 1000) / 1000
        lz = int(c * 1000) / 1000

        na = P['na']
        nb = P['nb']
        nc = P['nc']

        # Expand the cell along a
        xyz = list(atoms['coordinates'])
        tmp_bonds = list(bonds)
        for _ in range(1, na):
            # Atomic properties
            for key in atoms:
                if key == 'coordinates':
                    tmp = []
                    for x, y, z in xyz:
                        tmp.append((x + lx, y, z))
                    xyz = tmp
                    atoms[key].extend(xyz)
                elif key == 'atom_types':
                    types = atoms[key]
                    for type_ in types:
                        types[type_].extend(atoms[key][type_][0:n_atoms])
                else:
                    atoms[key].extend(atoms[key][0:n_atoms])
            # bonds
            tmp = []
            for i, j, order in tmp_bonds:
                tmp.append((i + n_atoms, j + n_atoms, order))
            tmp_bonds = tmp
            bonds.extend(tmp_bonds)

        # expand the cell along b
        n_atoms = len(atoms['elements'])
        xyz = list(atoms['coordinates'])
        tmp_bonds = list(bonds)
        for _ in range(1, nb):
            # Atomic properties
            for key in atoms:
                if key == 'coordinates':
                    tmp = []
                    for x, y, z in xyz:
                        tmp.append((x, y + ly, z))
                    xyz = tmp
                    atoms[key].extend(xyz)
                elif key == 'atom_types':
                    types = atoms[key]
                    for type_ in types:
                        types[type_].extend(atoms[key][type_][0:n_atoms])
                else:
                    atoms[key].extend(atoms[key][0:n_atoms])
            # bonds
            tmp = []
            for i, j, order in tmp_bonds:
                tmp.append((i + n_atoms, j + n_atoms, order))
            tmp_bonds = tmp
            bonds.extend(tmp_bonds)

        # expand the cell along c
        n_atoms = len(atoms['elements'])
        xyz = list(atoms['coordinates'])
        tmp_bonds = list(bonds)
        for _ in range(1, nc):
            # Atomic properties
            for key in atoms:
                if key == 'coordinates':
                    tmp = []
                    for x, y, z in xyz:
                        tmp.append((x, y, z + lz))
                    xyz = tmp
                    atoms[key].extend(xyz)
                elif key == 'atom_types':
                    types = atoms[key]
                    for type_ in types:
                        types[type_].extend(atoms[key][type_][0:n_atoms])
                else:
                    atoms[key].extend(atoms[key][0:n_atoms])
            # bonds
            tmp = []
            for i, j, order in tmp_bonds:
                tmp.append((i + n_atoms, j + n_atoms, order))
            tmp_bonds = tmp
            bonds.extend(tmp_bonds)

        # Update the cell
        n_atoms = len(atoms['elements'])
        a *= na
        b *= nb
        c *= nc
        system['cell'] = (a, b, c, alpha, beta, gamma)

        # Print what we did
        printer.important(
            __(
                (
                    f'Created a {na} x {nb} x {nc} supercell containing '
                    f'{n_atoms} atoms with cell parameters:'
                ),
                indent=self.indent + 4 * ' ',
            )
        )
        tmp = self.indent + 8 * ' '
        printer.important('')
        printer.important(tmp + f'    a = {a:8.3f} Å')
        printer.important(tmp + f'    b = {b:8.3f}')
        printer.important(tmp + f'    c = {c:8.3f}')
        printer.important(tmp + f'alpha = {alpha:7.2f} degrees')
        printer.important(tmp + f' beta = {beta:7.2f}')
        printer.important(tmp + f'gamma = {gamma:7.2f}')

        # Analyze the results
        self.analyze()

        return next_node
