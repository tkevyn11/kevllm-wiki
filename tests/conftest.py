"""Test helpers.

Typer 0.26 replaced ``CliRunner`` and dropped ``isolated_filesystem``.
The suite still uses that context manager to run each test in a scratch directory.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager

import typer.testing


if not hasattr(typer.testing.CliRunner, "isolated_filesystem"):

    @contextmanager
    def isolated_filesystem(self: typer.testing.CliRunner) -> Iterator[str]:
        previous = os.getcwd()
        directory = tempfile.mkdtemp()
        os.chdir(directory)
        try:
            yield directory
        finally:
            os.chdir(previous)
            shutil.rmtree(directory, ignore_errors=True)

    typer.testing.CliRunner.isolated_filesystem = isolated_filesystem  # type: ignore[attr-defined]
