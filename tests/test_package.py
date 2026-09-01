"""Tests that the epilogue package is importable and exposes its public API."""

from __future__ import annotations

import epilogue


def test_package_is_importable() -> None:
    assert epilogue is not None


def test_version_is_a_string() -> None:
    assert isinstance(epilogue.__version__, str)
    assert epilogue.__version__ == "0.1.0"


def test_public_api_reexports_data_model() -> None:
    """The package re-exports the data model at the top level."""
    from epilogue import Cycle, Entry, MergeStatus

    assert Cycle is epilogue.Cycle
    assert Entry is epilogue.Entry
    assert MergeStatus is epilogue.MergeStatus


def test_all_names_are_exported() -> None:
    for name in epilogue.__all__:
        assert hasattr(epilogue, name), f"missing export: {name}"
