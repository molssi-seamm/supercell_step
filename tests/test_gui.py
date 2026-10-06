# -*- coding: utf-8 -*-

"""Smoke test of the Tk dialog: create it and re-lay it out for every structure
handling choice. Skipped when no display is available."""

import pytest


@pytest.fixture()
def tk_node():
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available for Tk")
    root.withdraw()
    import Pmw
    import seamm

    Pmw.initialise(root)
    flowchart = seamm.Flowchart(namespace="org.molssi.seamm", directory=".")
    tk_flowchart = seamm.TkFlowchart(
        master=root, flowchart=flowchart, namespace="org.molssi.seamm.tk"
    )
    node = flowchart.create_node("Supercell")
    flowchart.add_node(node)
    plugin = tk_flowchart.plugin_manager.get("Supercell")
    tk_node = plugin.create_tk_node(
        tk_flowchart=tk_flowchart, node=node, canvas=tk_flowchart.canvas, x=100, y=100
    )
    yield tk_node
    root.destroy()


def test_dialog_layouts(tk_node):
    tk_node.create_dialog()
    choices = tk_node["structure handling"].combobox.cget("values")
    assert "Discard the structure" not in choices
    for handling in choices:
        tk_node["structure handling"].set(handling)
        tk_node.reset_dialog()
        shown = tk_node["system name"].grid_info() != {}
        assert shown == (handling == "Create a new system and configuration")
        assert tk_node["configuration name"].grid_info() != {}
    # A variable may choose any handling at run time, so the name is shown
    tk_node["structure handling"].set("$handling")
    tk_node.reset_dialog()
    assert tk_node["system name"].grid_info() != {}
