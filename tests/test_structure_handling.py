# -*- coding: utf-8 -*-

"""The supercell's handling: SEAMM's standard choices and names.

End to end, a flowchart (a tiny cubic crystal step, then Supercell) is built from
a spec and run by ``run_flowchart`` (seamm_exec.testing); the result is read from
the job's database.
"""

import sqlite3
import textwrap
from pathlib import Path

import pytest

from supercell_step import SUPERCELL_NAME, SupercellParameters

SOURCE = Path(__file__).resolve().parents[1]

CUBIC_STEP = textwrap.dedent('''
    """A step for testing: a cubic cell, a = 3 Å, holding one bonded pair."""

    import seamm


    class Cubic(seamm.Node):
        def __init__(self, flowchart=None, extension=None):
            super().__init__(flowchart=flowchart, title="Cubic", extension=extension)

        @property
        def version(self):
            return "0.1"

        def description_text(self, P=None):
            return self.header + "\\n    A cubic crystal."

        def run(self):
            next_node = super().run(None)
            db = self.get_variable("_system_db")
            system = db.create_system(name="argon")
            configuration = system.create_configuration(
                name="cubic", periodicity=3, coordinate_system="Fractional"
            )
            configuration.cell.parameters = [3.0, 3.0, 3.0, 90.0, 90.0, 90.0]
            ids = configuration.atoms.append(
                x=[0.25, 0.5], y=[0.0, 0.0], z=[0.0, 0.0], symbol=["N", "N"]
            )
            configuration.bonds.append(i=[ids[0]], j=[ids[1]], bondorder=[3])
            db.system = system
            return next_node


    class CubicStep:
        my_description = {
            "description": "A cubic crystal for tests",
            "group": "Building",
            "name": "Cubic",
        }

        def __init__(self, flowchart=None, gui=None):
            pass

        def description(self):
            return CubicStep.my_description

        def create_node(self, flowchart=None, **kwargs):
            return Cubic(flowchart=flowchart, **kwargs)

        def create_tk_node(self, canvas=None, **kwargs):
            raise NotImplementedError("no GUI for the test step")
''')


SYMMETRIC_PAIR = """\
        configuration.symmetry.group = "P -1"
        configuration.cell.parameters = [3.0, 3.0, 3.0, 90.0, 90.0, 90.0]
        ids = configuration.atoms.append(x=[0.1], y=[0.0], z=[0.0], symbol=["N"])
        configuration.bonds.append(
            i=[ids[0]], j=[ids[0]], bondorder=[3], symop1=["."], symop2=["2"]
        )
"""


def test_choices_and_defaults():
    P = SupercellParameters()
    handling = P["structure handling"]
    assert handling.value == "Overwrite the current configuration"
    assert tuple(handling.enumeration) == (
        "Overwrite the current configuration",
        "Create a new configuration",
        "Create a new system and configuration",
    )
    assert "subsequent structure handling" not in P
    assert P["configuration name"].value == "keep current name"
    assert SUPERCELL_NAME in P["configuration name"].enumeration


def run_supercell(
    tmp_path,
    na=2,
    nb=1,
    nc=1,
    coordinate_system="Fractional",
    symmetric=False,
    **parameters,
):
    testing = pytest.importorskip("seamm_exec.testing")
    site = tmp_path / "cubic_site"
    info = site / "seamm_test_cubic-0.1.dist-info"
    info.mkdir(parents=True)
    step = CUBIC_STEP
    if coordinate_system == "Cartesian":
        # The same pair, in Å
        step = step.replace(
            'coordinate_system="Fractional"', 'coordinate_system="Cartesian"'
        )
        step = step.replace("x=[0.25, 0.5]", "x=[0.75, 1.5]")
    if symmetric:
        # P -1: one N at (0.1, 0, 0) bonded to its inverse, 0.6 Å away
        old = step[
            step.index("        configuration.cell") : step.index("        db.system")
        ]
        step = step.replace(old, SYMMETRIC_PAIR)
    (site / "seamm_test_cubic.py").write_text(step)
    (info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: seamm-test-cubic\nVersion: 0.1\n"
    )
    (info / "entry_points.txt").write_text(
        "[org.molssi.seamm]\nCubic = seamm_test_cubic:CubicStep\n\n"
        "[org.molssi.seamm.tk]\nCubic = seamm_test_cubic:CubicStep\n"
    )
    lines = "".join(f"        {k}: '{v}'\n" for k, v in parameters.items())
    spec = (
        "title: Supercell test\nsteps:\n- Cubic: {}\n- Supercell:\n"
        f"        na: '{na}'\n        nb: '{nb}'\n        nc: '{nc}'\n" + lines
    )
    job = testing.run_spec(tmp_path, spec, source=SOURCE, extra_path=[site])
    db = sqlite3.connect(f"file:{job / 'seamm.db'}?mode=ro", uri=True)
    try:
        systems = db.execute("SELECT id, name FROM system ORDER BY id").fetchall()
        configurations = db.execute(
            "SELECT id, system, name, cell, atomset FROM configuration ORDER BY id"
        ).fetchall()
        cells = {
            row[0]: row[1:]
            for row in db.execute("SELECT id, a, b, c FROM cell").fetchall()
        }
        n_atoms = dict(
            db.execute(
                "SELECT atomset, COUNT(*) FROM atomset_atom GROUP BY atomset"
            ).fetchall()
        )
        # bonds per configuration, each between atoms of its own atomset
        n_bonds = {}
        for cid, atomset, bondset in db.execute(
            "SELECT id, atomset, bondset FROM configuration"
        ).fetchall():
            n_bonds[cid] = db.execute(
                "SELECT COUNT(*) FROM bondset_bond bb JOIN bond b ON b.id = bb.bond"
                " WHERE bb.bondset = ? AND b.i IN"
                " (SELECT atom FROM atomset_atom WHERE atomset = ?) AND b.j IN"
                " (SELECT atom FROM atomset_atom WHERE atomset = ?)",
                (bondset, atomset, atomset),
            ).fetchone()[0]
    finally:
        db.close()
    return job, systems, configurations, cells, n_atoms, n_bonds


def test_overwrite_is_the_default(tmp_path):
    job, systems, configurations, cells, n_atoms, n_bonds = run_supercell(tmp_path)
    assert len(systems) == 1 and len(configurations) == 1
    (only,) = configurations
    assert only[2] == "cubic"  # the name is kept
    assert cells[only[3]][:2] == pytest.approx((6.0, 3.0))
    assert n_atoms[only[4]] == 4 and n_bonds[only[0]] == 2


def test_new_configuration_leaves_the_original(tmp_path):
    job, systems, configurations, cells, n_atoms, n_bonds = run_supercell(
        tmp_path,
        **{
            "structure handling": "Create a new configuration",
            "configuration name": SUPERCELL_NAME,
        },
    )
    assert len(systems) == 1
    first, second = configurations
    assert second[2] == "2 x 1 x 1 supercell"
    # The original is untouched: its own cell, atoms and bond
    assert cells[first[3]][0] == pytest.approx(3.0)
    assert n_atoms[first[4]] == 2 and n_bonds[first[0]] == 1
    assert first[4] != second[4]
    assert cells[second[3]][0] == pytest.approx(6.0)
    assert n_atoms[second[4]] == 4 and n_bonds[second[0]] == 2


def test_new_system_keeps_the_names(tmp_path):
    job, systems, configurations, cells, n_atoms, n_bonds = run_supercell(
        tmp_path, **{"structure handling": "Create a new system and configuration"}
    )
    assert [name for _, name in systems] == ["argon", "argon"]
    first, second = configurations
    assert second[1] == systems[1][0] and second[2] == "cubic"
    assert n_atoms[first[4]] == 2 and n_atoms[second[4]] == 4
    assert n_bonds[first[0]] == 1 and n_bonds[second[0]] == 2


@pytest.mark.parametrize("coordinate_system", ["Fractional", "Cartesian"])
@pytest.mark.parametrize(
    "handling", ["Overwrite the current configuration", "Create a new configuration"]
)
def test_bonds_in_a_3x2x1_supercell(tmp_path, coordinate_system, handling):
    """Each copy's bond joins its own pair: 6 bonds of 0.75 Å among 12 atoms."""
    import numpy as np
    from molsystem import SystemDB

    job, systems, configurations, cells, n_atoms, n_bonds = run_supercell(
        tmp_path,
        na=3,
        nb=2,
        nc=1,
        coordinate_system=coordinate_system,
        **{"structure handling": handling},
    )
    last = configurations[-1]
    assert n_atoms[last[4]] == 12 and n_bonds[last[0]] == 6
    db = SystemDB(filename=str(job / "seamm.db"))
    try:
        configuration = db.system.configuration
        xyz = np.array(configuration.atoms.get_coordinates(fractionals=False))
        index = {atom: i for i, atom in enumerate(configuration.atoms.ids)}
        bonds = configuration.bonds.get_as_dict()
        lengths = [
            np.linalg.norm(xyz[index[i]] - xyz[index[j]])
            for i, j in zip(bonds["i"], bonds["j"])
        ]
    finally:
        db.close()
    assert lengths == pytest.approx([0.75] * 6)


def test_overwrite_a_symmetric_structure_with_bonds(tmp_path):
    """P -1, lowered to P1 in place (molsystem >= 2026.10.6), then 2 x 1 x 1."""
    from molsystem import SystemDB

    job, systems, configurations, cells, n_atoms, n_bonds = run_supercell(
        tmp_path, symmetric=True
    )
    (only,) = configurations
    assert n_atoms[only[4]] == 4 and n_bonds[only[0]] == 2
    db = SystemDB(filename=str(job / "seamm.db"))
    try:
        configuration = db.system.configuration
        assert configuration.symmetry.n_symops == 1  # no symmetry left
        lengths = configuration.bonds.get_lengths()
    finally:
        db.close()
    assert lengths == pytest.approx([0.6, 0.6])
