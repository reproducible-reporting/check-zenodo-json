# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: Apache-2.0
"""Test the two copies of the Apache-2.0 text that this repository has to keep."""

from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def test_license_copies_are_identical():
    github = REPO_ROOT / "LICENSE"
    reuse = REPO_ROOT / "LICENSES" / "Apache-2.0.txt"
    assert github.read_bytes() == reuse.read_bytes()
