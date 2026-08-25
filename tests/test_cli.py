# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the `check-zenodo-json` command line interface."""

import sys

import pytest

from check_zenodo_json.__main__ import main

VALID = '{"upload_type": "software", "title": "Example"}'
INVALID = '{"upload_type": "blogpost"}'


def check(monkeypatch, tmp_path, contents: str) -> int:
    """Validate a `.zenodo.json` file with the given contents and return the exit code."""
    path = tmp_path / ".zenodo.json"
    path.write_text(contents)
    monkeypatch.setattr(sys, "argv", ["check-zenodo-json", str(path)])
    with pytest.raises(SystemExit) as exc_info:
        main()
    return exc_info.value.code


def test_valid(monkeypatch, tmp_path):
    assert check(monkeypatch, tmp_path, VALID) == 0


def test_invalid(monkeypatch, tmp_path, capsys):
    assert check(monkeypatch, tmp_path, INVALID) != 0
    assert "upload_type" in capsys.readouterr().out


def test_own_schemafile_refused(monkeypatch, tmp_path, capsys):
    path = tmp_path / ".zenodo.json"
    path.write_text(VALID)
    monkeypatch.setattr(sys, "argv", ["check-zenodo-json", "--schemafile", str(path), str(path)])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2
    assert "--schemafile" in capsys.readouterr().err
