# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: Apache-2.0
"""Command line interface of `check-zenodo-json`."""

import sys
from importlib.resources import as_file, files
from typing import NoReturn

from check_jsonschema import main as check_jsonschema

from . import SCHEMA_NAME

__all__ = ("main",)


def main() -> NoReturn:
    """Validate the files given on the command line against the Zenodo JSON Schema.

    All arguments are handed over to `check-jsonschema`,
    with the schema of this package prepended,
    so its options can be used to tweak the validation and the reporting.
    A `--schemafile` of your own is refused,
    because `check-jsonschema` honours the last one it is given,
    which would quietly validate against something other than the Zenodo schema.

    Raises
    ------
    SystemExit
        Always, carrying the exit code of `check-jsonschema`,
        or 2 when the arguments name a schema file.
    """
    if any(arg == "--schemafile" or arg.startswith("--schemafile=") for arg in sys.argv[1:]):
        print(
            "check-zenodo-json validates against its own schema, so --schemafile is not accepted.\n"
            "Run check-jsonschema directly to use a different schema.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    with as_file(files(__package__) / SCHEMA_NAME) as schema_path:
        check_jsonschema(
            ["--schemafile", str(schema_path), *sys.argv[1:]],
            prog_name="check-zenodo-json",
        )


if __name__ == "__main__":
    main()
