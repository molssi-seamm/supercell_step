# -*- coding: utf-8 -*-

"""Non-graphical part of the Supercell step in a SEAMM flowchart"""

import logging
import pprint  # noqa: F401

import seamm
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
printer = printing.getPrinter("Supercell")


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

    def __init__(
        self, flowchart=None, title="Supercell", extension=None, logger=logger
    ):
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
            title="Supercell",
            extension=extension,
            logger=logger,
        )

        self.parameters = supercell_step.SupercellParameters()

    @property
    def version(self):
        """The semantic version of this module."""
        return supercell_step.__version__

    @property
    def git_revision(self):
        """The git version of this module."""
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

        text = "Create a {na} x {nb} x {nc} supercell from the current cell"

        return self.header + "\n" + __(text, **P, indent=4 * " ").__str__()

    def run(self):
        """Create the supercell.

        The strategy used is to expand in the `a` direction, adding the atoms
        and bonds from the original system for each cell add, and keeping the
        new fractional coordinates. Then move to the `b` direction, getting the
        current atoms and bonds for the expanded `a` direction. And finally for
        the `c` direction. At the end, after setting the cell the coordinates
        are updated with the fractional coordinates that have been accumulated.

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
        system_db = self.get_variable("_system_db")
        configuration = system_db.system.configuration

        if configuration.periodicity != 3:
            raise ValueError("System is not periodic. Cannot make a supercell!")

        na = P["na"]
        nb = P["nb"]
        nc = P["nc"]
        logger.debug(f"making {na} x {nb} x {nc} supercell")

        # Lower the symmetry if needed
        if configuration.symmetry.group != "P 1":
            configuration.lower_symmetry()

        atoms = configuration.atoms
        bonds = configuration.bonds
        cell = configuration.cell

        # Get a copy of the initial atom and bond data
        atom_data = atoms.get_as_dict()
        # index of atoms to use for bonds
        index = {j: i for i, j in enumerate(atom_data["id"])}
        del atom_data["id"]
        bond_data = bonds.get_as_dict()
        del bond_data["id"]

        # Get the initial fractional coordinates, adjusting to the final cell
        xyz0 = [
            [x / na, y / nb, z / nc]
            for x, y, z in zip(atom_data["x"], atom_data["y"], atom_data["z"])
        ]
        xyzs = list(xyz0)

        # Expand the cell along 'a'
        if na > 1:
            for ia in range(1, na):
                # Coordinates
                for x, y, z in xyz0:
                    xyzs.append([x + ia / na, y, z])
                # Atoms
                ids = atoms.append(**atom_data)
                # Bonds
                bond_data["i"] = [ids[index[i]] for i in bond_data["i"]]
                bond_data["j"] = [ids[index[j]] for j in bond_data["j"]]
                bonds.append(**bond_data)

            # Get a copy of the current atom and bond data
            atom_data = atoms.get_as_dict()
            # index of atoms to use for bonds
            index = {j: i for i, j in enumerate(atom_data["id"])}
            del atom_data["id"]
            bond_data = bonds.get_as_dict()
            del bond_data["id"]

            # Keep a copy of the current coordinates
            xyz0 = list(xyzs)

        # Expand the cell along 'b'
        if nb > 1:
            for ib in range(1, nb):
                # Coordinates
                for x, y, z in xyz0:
                    xyzs.append([x, y + ib / nb, z])
                # Atoms
                ids = atoms.append(**atom_data)
                # Bonds
                bond_data["i"] = [ids[index[i]] for i in bond_data["i"]]
                bond_data["j"] = [ids[index[j]] for j in bond_data["j"]]
                bonds.append(**bond_data)

            # Get a copy of the current atom and bond data
            atom_data = atoms.get_as_dict()
            # index of atoms to use for bonds
            index = {j: i for i, j in enumerate(atom_data["id"])}
            del atom_data["id"]
            bond_data = bonds.get_as_dict()
            del bond_data["id"]

            # Keep a copy of the current coordinates
            xyz0 = list(xyzs)

        # Expand the cell along 'c'
        if nc > 1:
            for ic in range(1, nc):
                # Coordinates
                for x, y, z in xyz0:
                    xyzs.append([x, y, z + ic / nc])
                # Atoms
                ids = atoms.append(**atom_data)
                # Bonds
                bond_data["i"] = [ids[index[i]] for i in bond_data["i"]]
                bond_data["j"] = [ids[index[j]] for j in bond_data["j"]]
                bonds.append(**bond_data)

        # Update the cell
        a, b, c, alpha, beta, gamma = cell.parameters
        logger.debug(f"initial cell: {a}, {b}, {c}, {alpha}, {beta}, {gamma}")
        a *= na
        b *= nb
        c *= nc
        logger.debug(f"final cell: {a}, {b}, {c}, {alpha}, {beta}, {gamma}")
        cell.parameters = (a, b, c, alpha, beta, gamma)

        # Set all the coordinates using the new cell
        atoms.set_coordinates(xyzs, fractionals=True)

        # Print what we did
        n_atoms = atoms.n_atoms
        printer.important(
            __(
                (
                    f"Created a {na} x {nb} x {nc} supercell containing "
                    f"{n_atoms} atoms with cell parameters:"
                ),
                indent=self.indent + 4 * " ",
            )
        )
        tmp = self.indent + 8 * " "
        printer.important("")
        printer.important(tmp + f"    a = {a:8.3f} Å")
        printer.important(tmp + f"    b = {b:8.3f}")
        printer.important(tmp + f"    c = {c:8.3f}")
        printer.important(tmp + f"alpha = {alpha:7.2f} degrees")
        printer.important(tmp + f" beta = {beta:7.2f}")
        printer.important(tmp + f"gamma = {gamma:7.2f}")
        printer.important("")

        # Analyze the results
        self.analyze()

        return next_node
