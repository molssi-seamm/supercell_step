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

        text = "Create a {na} x {nb} x {nc} supercell from the current cell."
        if "structure handling" in P:
            text += " " + seamm.standard_parameters.structure_handling_description(P)

        return self.header + "\n" + __(text, **P, indent=4 * " ").__str__()

    def _p1_copy(self, system, other):
        """A new, current configuration of ``system``: ``other`` in P1, with
        atoms, bonds and cell of its own.

        The supercell adds atoms and bonds, which a copy sharing the atoms
        (``copy_configuration``) would add to the original too. This is what
        ``lower_symmetry(other=...)`` intends, but molsystem's copies the source's
        configuration id with the atoms, so their coordinates land on the source.
        """
        configuration = system.create_configuration(
            periodicity=3,
            coordinate_system=other.coordinate_system,
            make_current=True,
        )
        configuration.cell.parameters = other.cell.parameters

        # The atoms and bonds in low symmetry
        atom_data = other.atoms.get_as_dict()
        del atom_data["id"]
        del atom_data["configuration"]
        for key in ("vx", "vy", "vz", "gx", "gy", "gz"):
            atom_data.pop(key, None)
        bond_data = other.bonds.get_as_dict()
        del bond_data["id"]

        ids = configuration.atoms.append(**atom_data)
        # get_as_dict() gives a periodic system's fractional coordinates, which
        # append() takes as Cartesian in a Cartesian configuration, so set them
        configuration.atoms.set_coordinates(
            other.atoms.get_coordinates(fractionals=True), fractionals=True
        )
        if len(bond_data["i"]) > 0:
            atom_ids = other.atoms.ids
            index = {j: i for i, j in enumerate(atom_ids)}
            bond_data["i"] = [ids[index[i]] for i in bond_data["i"]]
            bond_data["j"] = [ids[index[j]] for j in bond_data["j"]]
            configuration.bonds.append(**bond_data)

        configuration.charge = other.charge
        configuration.spin_multiplicity = other.spin_multiplicity
        configuration.n_active_electrons = other.n_active_electrons
        configuration.n_active_orbitals = other.n_active_orbitals
        return configuration

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

        # The current system and configuration
        system_db = self.get_variable("_system_db")
        starting_system, starting = self.get_system_configuration(None)

        if starting.periodicity != 3:
            raise ValueError("System is not periodic. Cannot make a supercell!")

        na = P["na"]
        nb = P["nb"]
        nc = P["nc"]
        logger.debug(f"making {na} x {nb} x {nc} supercell")

        handling = P["structure handling"]
        if handling == "Overwrite the current configuration":
            system, configuration = starting_system, starting
            # Lower the symmetry if needed
            if configuration.symmetry.group != "P 1":
                configuration.lower_symmetry()
        else:
            if handling == "Create a new system and configuration":
                system = system_db.create_system()
            else:
                system = starting_system
            configuration = self._p1_copy(system, starting)
            system_db.system = system

        atoms = configuration.atoms
        bonds = configuration.bonds
        cell = configuration.cell

        # Get a copy of the initial atom and bond data
        atom_data = atoms.get_as_dict()
        # index of atoms to use for bonds
        # The bonds name atoms by id; get_as_dict()["id"] holds row positions
        index = {j: i for i, j in enumerate(atoms.ids)}
        del atom_data["id"]
        bond_data = bonds.get_as_dict()
        del bond_data["id"]

        # Remove the gradients, if they exist
        if "gx" in atom_data:
            del atom_data["gx"]
            del atom_data["gy"]
            del atom_data["gz"]

        # Get the initial fractional coordinates, adjusting to the final cell
        xyz0 = [
            [x / na, y / nb, z / nc]
            for x, y, z in zip(atom_data["x"], atom_data["y"], atom_data["z"])
        ]
        xyzs = list(xyz0)

        # Expand the cell along 'a'
        if na > 1:
            # Each copy's bonds are mapped from the original's, not the last copy's
            bond_i, bond_j = bond_data["i"], bond_data["j"]
            for ia in range(1, na):
                # Coordinates
                for x, y, z in xyz0:
                    xyzs.append([x + ia / na, y, z])
                # Atoms
                ids = atoms.append(**atom_data)
                # Bonds
                bond_data["i"] = [ids[index[i]] for i in bond_i]
                bond_data["j"] = [ids[index[j]] for j in bond_j]
                bonds.append(**bond_data)

            # Get a copy of the current atom and bond data
            atom_data = atoms.get_as_dict()
            # index of atoms to use for bonds
            # The bonds name atoms by id; get_as_dict()["id"] holds row positions
            index = {j: i for i, j in enumerate(atoms.ids)}
            del atom_data["id"]
            bond_data = bonds.get_as_dict()
            del bond_data["id"]

            # Remove the gradients, if they exist
            if "gx" in atom_data:
                del atom_data["gx"]
                del atom_data["gy"]
                del atom_data["gz"]

            # Keep a copy of the current coordinates
            xyz0 = list(xyzs)

        # Expand the cell along 'b'
        if nb > 1:
            # Each copy's bonds are mapped from the original's, not the last copy's
            bond_i, bond_j = bond_data["i"], bond_data["j"]
            for ib in range(1, nb):
                # Coordinates
                for x, y, z in xyz0:
                    xyzs.append([x, y + ib / nb, z])
                # Atoms
                ids = atoms.append(**atom_data)
                # Bonds
                bond_data["i"] = [ids[index[i]] for i in bond_i]
                bond_data["j"] = [ids[index[j]] for j in bond_j]
                bonds.append(**bond_data)

            # Get a copy of the current atom and bond data
            atom_data = atoms.get_as_dict()
            # index of atoms to use for bonds
            # The bonds name atoms by id; get_as_dict()["id"] holds row positions
            index = {j: i for i, j in enumerate(atoms.ids)}
            del atom_data["id"]
            bond_data = bonds.get_as_dict()
            del bond_data["id"]

            # Remove the gradients, if they exist
            if "gx" in atom_data:
                del atom_data["gx"]
                del atom_data["gy"]
                del atom_data["gz"]

            # Keep a copy of the current coordinates
            xyz0 = list(xyzs)

        # Expand the cell along 'c'
        if nc > 1:
            # Each copy's bonds are mapped from the original's, not the last copy's
            bond_i, bond_j = bond_data["i"], bond_data["j"]
            for ic in range(1, nc):
                # Coordinates
                for x, y, z in xyz0:
                    xyzs.append([x, y, z + ic / nc])
                # Atoms
                ids = atoms.append(**atom_data)
                # Bonds
                bond_data["i"] = [ids[index[i]] for i in bond_i]
                bond_data["j"] = [ids[index[j]] for j in bond_j]
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

        # Names: "keep current name" carries the names over to a new system or
        # configuration
        names = dict(P)
        if names["configuration name"] == supercell_step.SUPERCELL_NAME:
            names["configuration name"] = f"{na} x {nb} x {nc} supercell"
        if (
            system is not starting_system
            and names["system name"] == "keep current name"
        ):
            system.name = starting_system.name
        if configuration.id != starting.id and names["configuration name"] == (
            "keep current name"
        ):
            configuration.name = starting.name
        text = seamm.standard_parameters.set_names(system, configuration, names)
        printer.important(__(text, indent=self.indent + 4 * " "))
        printer.important("")

        # Analyze the results
        self.analyze()

        return next_node
