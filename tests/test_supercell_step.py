#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `supercell_step` package."""

import pytest  # noqa: F401
import supercell_step  # noqa: F401
import re


@pytest.fixture
def instance():
    instance = supercell_step.Supercell()
    instance._id = (1,)
    return instance


def test_construction():
    """Simplest test that we can make a SUPERCELL object"""
    instance = supercell_step.Supercell()
    assert (
        str(type(instance)) == "<class 'supercell_step.supercell.Supercell'>"
    )


def test_version():
    """Test that the object returns a version"""
    instance = supercell_step.Supercell()
    result = instance.version
    assert isinstance(result, str) and len(result) > 0


def test_git_revision():
    """Test that the object returns a git revision"""
    instance = supercell_step.Supercell()
    result = instance.git_revision
    assert isinstance(result, str) and len(result) > 0


def test_description_text_default(instance):
    """Test the default description text"""

    assert re.fullmatch(
        (
            r'Step 1: Supercell  [-+.0-9a-z]+\n'
            r'    Create a 2 x 2 x 2 supercell from the current cell'
        ), instance.description_text()
    ) is not None


def test_description_text_expr_expr(instance):
    """Test the default description text"""

    assert re.fullmatch(
        (
            r'Step 1: Supercell  [-+.0-9a-z]+\n'
            r'    Create a 5 x 4 x 3 supercell from the current cell'
        ), instance.description_text({
            'na': 5,
            'nb': 4,
            'nc': 3,
        })
    ) is not None
