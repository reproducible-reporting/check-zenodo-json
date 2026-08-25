# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: Apache-2.0
"""Tests for the JSON Schema of `.zenodo.json`.

The schema is validated by the `check-jsonschema` pre-commit hook,
which only sees the repository's own `.zenodo.json`.
These tests pin down what the schema accepts and rejects beyond that one file.
"""

import json
from importlib.resources import files
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from check_zenodo_json import SCHEMA_NAME

REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = files("check_zenodo_json") / SCHEMA_NAME

MINIMAL = {"upload_type": "software", "title": "Example"}

# Zenodo's own documented example, which is rejected on purpose.
# It puts a `type` on a creator, but creators have no role in InvenioRDM,
# so `CreatorSchema` in zenodo-rdm drops the key without saying anything.
DOCS_EXAMPLE = {
    "creators": [
        {
            "name": "Carberry, Josiah",
            "orcid": "0000-0002-1825-0097",
            "affiliation": "Brown University",
            "type": "ProjectMember",
        }
    ],
    "contributors": [
        {"name": "Lovelace, Ada", "type": "Researcher"},
        {
            "name": "Babbage, Charles",
            "affiliation": "University of Cambridge",
            "type": "ProjectLeader",
        },
    ],
    "title": "Memory bus simulation scripts",
    "version": "1.8.0",
    "access_right": "open",
    "related_identifiers": [
        {
            "identifier": "https://doi.org/10.5555/666655554444",
            "relation": "isSupplementTo",
            "resource_type": "publication-article",
        }
    ],
    "keywords": ["computer science", "psychoceramics", "journaling filesystems"],
    "license": "mit",
    "upload_type": "software",
    "language": "eng",
    "grants": [{"id": "10.13039/501100000780::101122956"}],
    "communities": [{"identifier": "simulation-software"}],
}

ACCEPTED = [
    (
        "docs example without the creator role",
        {**DOCS_EXAMPLE, "creators": [{"name": "Carberry, Josiah"}]},
    ),
    ("license in lower case", {**MINIMAL, "license": "lgpl-3.0-or-later"}),
    ("license as an object", {**MINIMAL, "license": {"id": "mit"}}),
    # `fal` and `gfdl` alias to identifiers that are absent from the RDM map,
    # so Zenodo falls back to the legacy vocabulary and keeps the license as a free-text title.
    ("license only in the legacy vocabulary", {**MINIMAL, "license": "gfdl"}),
    # Postdates the legacy vocabulary but is in the InvenioRDM one.
    (
        "relation isVersionOf",
        {
            **MINIMAL,
            "related_identifiers": [{"identifier": "10.5281/zenodo.1", "relation": "isVersionOf"}],
        },
    ),
    # Zenodo patches this misspelling before the lookup, so it stays valid input.
    (
        "misspelled legacy relation",
        {
            **MINIMAL,
            "related_identifiers": [
                {"identifier": "10.5281/zenodo.1", "relation": "isOrignialFormOf"}
            ],
        },
    ),
    (
        "related identifier with a resource type",
        {
            **MINIMAL,
            "related_identifiers": [
                {
                    "identifier": "10.5281/zenodo.1",
                    "relation": "cites",
                    "resource_type": "publication-softwaredocumentation",
                }
            ],
        },
    ),
    ("embargo with a date", {**MINIMAL, "access_right": "embargoed", "embargo_date": "2027-01-01"}),
    (
        "creator with all identifiers",
        {
            **MINIMAL,
            "creators": [
                {
                    "name": "Doe, Jane",
                    "orcid": "0000-0001-9288-5608",
                    "affiliation": "X",
                    "gnd": "118540238",
                }
            ],
        },
    ),
    (
        "creator with a gnd in the other shape",
        {**MINIMAL, "creators": [{"name": "X", "gnd": "4079154-3"}]},
    ),
    (
        "creator with an orcid url",
        {**MINIMAL, "creators": [{"name": "X", "orcid": "https://orcid.org/0000-0001-9288-5608"}]},
    ),
    (
        "creator with an unhyphenated orcid",
        {**MINIMAL, "creators": [{"name": "X", "orcid": "0000000192885608"}]},
    ),
    (
        "contributor with a role",
        {**MINIMAL, "contributors": [{"name": "Doe, Jane", "type": "ProjectLeader"}]},
    ),
    # `annotator` is in the role vocabulary Zenodo deploys,
    # even though the Zenodo documentation does not list it and DataCite has no equivalent.
    (
        "contributor with the annotator role",
        {**MINIMAL, "contributors": [{"name": "Doe, Jane", "type": "Annotator"}]},
    ),
    (
        "publication subtype added after the legacy list",
        {"upload_type": "publication", "publication_type": "datapaper"},
    ),
    ("software subtype", {"upload_type": "software", "software_type": "computationalnotebook"}),
    ("image subtype", {"upload_type": "image", "image_type": "figure"}),
    (
        "date range",
        {**MINIMAL, "dates": [{"type": "collected", "start": "2024-01-01", "end": "2024-02-01"}]},
    ),
    # RDM validates dates as EDTF level 0, which allows a reduced precision.
    (
        "date range without days",
        {**MINIMAL, "dates": [{"type": "collected", "start": "2024-01", "end": "2024-02"}]},
    ),
    ("publication date without a day", {**MINIMAL, "publication_date": "2026-08"}),
    ("publication date as a year", {**MINIMAL, "publication_date": "2026"}),
    ("publication date as an interval", {**MINIMAL, "publication_date": "2026-01/2026-02"}),
    ("two letter language", {**MINIMAL, "language": "en"}),
    ("three letter language", {**MINIMAL, "language": "eng"}),
    # A bare award id is read as a European Commission grant.
    ("grant without a funder prefix", {**MINIMAL, "grants": [{"id": "101122956"}]}),
    (
        "location with coordinates",
        {**MINIMAL, "locations": [{"place": "Ghent", "lat": 51.05, "lon": 3.72}]},
    ),
    ("location without coordinates", {**MINIMAL, "locations": [{"place": "Ghent"}]}),
    (
        "subject from a vocabulary",
        {**MINIMAL, "subjects": [{"term": "X", "identifier": "http://x", "scheme": "url"}]},
    ),
    # `load_subjects` reads term, identifier and scheme with `.get`, so none of them is required.
    ("subject with only a term", {**MINIMAL, "subjects": [{"term": "X"}]}),
    ("custom fields", {**MINIMAL, "custom": {"dwc:family": ["Felidae"]}}),
    (
        "custom field from the codemeta namespace",
        {**MINIMAL, "custom": {"code:developmentStatus": {"id": "active"}}},
    ),
    (
        "custom field holding a bare string",
        {**MINIMAL, "custom": {"code:codeRepository": "https://x.y/z"}},
    ),
    # `validate_metadata_schema` fires only when the loaded metadata is exactly one `publisher` key,
    # which cannot happen because `publication_date` is defaulted as well.
    # Zenodo then falls back to the metadata it derives from the GitHub repository.
    ("empty metadata", {}),
    (
        "alternate identifier",
        {**MINIMAL, "alternate_identifiers": [{"identifier": "arXiv:1234.5678"}]},
    ),
    # Zenodo strips a description, a note and a method shorter than three characters.
    (
        "free text descriptions",
        {**MINIMAL, "notes": "See below.", "method": "MD", "references": ["Doe, J. (2024)."]},
    ),
    (
        "container metadata",
        {
            **MINIMAL,
            "journal_title": "J",
            "conference_title": "C",
            "imprint_isbn": "978-3-16-148410-0",
            "partof_title": "P",
            "thesis_university": "U",
        },
    ),
]

REJECTED = [
    ("creator role that Zenodo discards", DOCS_EXAMPLE),
    # Zenodo lower cases and strips before it maps the license to an InvenioRDM identifier,
    # so it accepts these spellings too.
    # The schema asks for the identifier as it will appear in the deposit.
    ("license in SPDX case", {**MINIMAL, "license": "LGPL-3.0-or-later"}),
    ("license in upper case", {**MINIMAL, "license": "AGPL-3.0"}),
    ("license with surrounding space", {**MINIMAL, "license": " mit "}),
    ("unknown license", {**MINIMAL, "license": "nope-1.0"}),
    (
        "unknown relation",
        {
            **MINIMAL,
            "related_identifiers": [
                {"identifier": "10.5281/zenodo.1", "relation": "isSupplementOf"}
            ],
        },
    ),
    # Zenodo lower cases a relation, a contributor role and a date type before the lookup,
    # so it accepts any capitalisation of the three.
    # The schema asks for the spelling of the Zenodo documentation.
    (
        "relation in another case",
        {
            **MINIMAL,
            "related_identifiers": [{"identifier": "10.5281/zenodo.1", "relation": "IsCitedBy"}],
        },
    ),
    (
        "related identifier without an identifier",
        {**MINIMAL, "related_identifiers": [{"relation": "cites"}]},
    ),
    (
        "unknown resource type",
        {
            **MINIMAL,
            "related_identifiers": [
                {
                    "identifier": "10.5281/zenodo.1",
                    "relation": "cites",
                    "resource_type": "publication-blogpost",
                }
            ],
        },
    ),
    # `split_identifiers` moves the entry to `alternate_identifiers`,
    # where `load_alternate_identifiers` reads only the identifier.
    (
        "resource type on an alternate identifier relation",
        {
            **MINIMAL,
            "related_identifiers": [
                {
                    "identifier": "10.5281/zenodo.1",
                    "relation": "isAlternateIdentifier",
                    "resource_type": "dataset",
                }
            ],
        },
    ),
    # Zenodo raises "Unknown access type" when the date is missing.
    ("embargo without a date", {**MINIMAL, "access_right": "embargoed"}),
    # `load_access` reads `embargo_date` only in the embargoed branch, so it is dropped otherwise.
    (
        "embargo date without an embargo",
        {**MINIMAL, "access_right": "open", "embargo_date": "2027-01-01"},
    ),
    (
        "embargo date with an impossible month",
        {**MINIMAL, "access_right": "embargoed", "embargo_date": "2027-13-01"},
    ),
    ("unknown access right", {**MINIMAL, "access_right": "public"}),
    ("misspelled key", {**MINIMAL, "keyword": ["a"]}),
    # The loader detects the scheme from the identifier itself and never reads the key,
    # so this DOI is stored with scheme `doi` however the key is spelled.
    (
        "scheme on a related identifier",
        {
            **MINIMAL,
            "related_identifiers": [
                {"identifier": "10.5281/zenodo.1", "relation": "cites", "scheme": "arxiv"}
            ],
        },
    ),
    (
        "scheme on an alternate identifier",
        {
            **MINIMAL,
            "alternate_identifiers": [{"identifier": "arXiv:1234.5678", "scheme": "arxiv"}],
        },
    ),
    # RDM has no equivalent, so the key is dropped without a word.
    ("access conditions", {**MINIMAL, "access_right": "restricted", "access_conditions": "Ask."}),
    # `load_custom_fields` copies `custom` verbatim into the deposit it builds,
    # so an unknown name is never looked up and the field simply disappears.
    ("unknown custom field", {**MINIMAL, "custom": {"dwc:famliy": ["Felidae"]}}),
    ("creator without a name", {**MINIMAL, "creators": [{"orcid": "0000-0001-9288-5608"}]}),
    (
        "unknown contributor role",
        {**MINIMAL, "contributors": [{"name": "Doe, Jane", "type": "Maintainer"}]},
    ),
    (
        "contributor role in another case",
        {**MINIMAL, "contributors": [{"name": "Doe, Jane", "type": "projectleader"}]},
    ),
    ("unknown upload type", {"upload_type": "blogpost"}),
    # `load_upload_type` builds the resource type as `<upload_type>-<subtype>`,
    # and `publication-thesis` is absent from the invenio-rdm-records vocabulary,
    # which spells the same concept `publication-dissertation`.
    ("thesis publication subtype", {"upload_type": "publication", "publication_type": "thesis"}),
    # `load_upload_type` reads only `<upload_type>_type`, so any other subtype is dropped.
    ("subtype of another upload type", {**MINIMAL, "image_type": "figure"}),
    ("subtype without an upload type", {"publication_type": "article"}),
    # RDM implements EDTF level 0, which has no open intervals.
    ("date without a start or end", {**MINIMAL, "dates": [{"type": "collected"}]}),
    ("unknown date type", {**MINIMAL, "dates": [{"type": "harvested", "start": "2024-01-01"}]}),
    (
        "date type in another case",
        {**MINIMAL, "dates": [{"type": "Collected", "start": "2024-01-01"}]},
    ),
    ("language that is neither ISO 639-1 nor 639-2", {**MINIMAL, "language": "engl"}),
    # A three letter code reaches the languages vocabulary unchanged,
    # and a two letter code is looked up by its lower case form,
    # so an upper case code resolves to nothing either way.
    ("language in upper case", {**MINIMAL, "language": "ENG"}),
    ("publication date that is not ISO 8601", {**MINIMAL, "publication_date": "23/08/2026"}),
    ("publication date with an impossible month", {**MINIMAL, "publication_date": "2026-13"}),
    ("grant without an id", {**MINIMAL, "grants": [{}]}),
    (
        "community keyed by id instead of identifier",
        {**MINIMAL, "communities": [{"id": "biosyslit"}]},
    ),
    ("location without a place", {**MINIMAL, "locations": [{"lat": 51.05}]}),
    # `load_locations` builds the point under `if lat and lon`, so a lone coordinate is dropped.
    ("location with only a latitude", {**MINIMAL, "locations": [{"place": "Ghent", "lat": 51.05}]}),
    # The four vocabularies below come from whichever invenio-rdm-records fixture
    # Zenodo's instance was built with, so they lag that project's main branch.
    # Zenodo answers "Invalid value ..." for every entry that has not reached it yet.
    ("upload type Zenodo has not deployed", {"upload_type": "audio", "title": "Example"}),
    ("instrument upload type", {"upload_type": "instrument", "title": "Example"}),
    ("project upload type", {"upload_type": "project", "title": "Example"}),
    (
        "publication subtype Zenodo has not deployed",
        {"upload_type": "publication", "publication_type": "studyregistration"},
    ),
    (
        "resource type Zenodo has not deployed",
        {
            **MINIMAL,
            "related_identifiers": [
                {
                    "identifier": "10.5281/zenodo.1",
                    "relation": "cites",
                    "resource_type": "publication-studyregistration",
                }
            ],
        },
    ),
    (
        "relation Zenodo has not deployed",
        {
            **MINIMAL,
            "related_identifiers": [{"identifier": "10.5281/zenodo.1", "relation": "collects"}],
        },
    ),
    # DataCite has an "other" relation and invenio-rdm-records carries it, Zenodo does not.
    (
        "relation other",
        {
            **MINIMAL,
            "related_identifiers": [{"identifier": "10.5281/zenodo.1", "relation": "other"}],
        },
    ),
    (
        "date type Zenodo has not deployed",
        {**MINIMAL, "dates": [{"type": "coverage", "start": "2024"}]},
    ),
    (
        "contributor role Zenodo has not deployed",
        {**MINIMAL, "contributors": [{"name": "Doe, Jane", "type": "Translator"}]},
    ),
    # `normalize_orcid` is applied without checking the value first,
    # so a malformed ORCID reaches the record mangled and takes the creator's name with it.
    ("malformed orcid", {**MINIMAL, "creators": [{"name": "Doe, Jane", "orcid": "1234"}]}),
    (
        "orcid with too few digits",
        {**MINIMAL, "creators": [{"name": "Doe, Jane", "orcid": "0000-0001-9288-560"}]},
    ),
    # `normalize_gnd` indexes the match without testing it, so a bad GND is a server error.
    ("malformed gnd", {**MINIMAL, "creators": [{"name": "Doe, Jane", "gnd": "1"}]}),
    (
        "gnd in a prefix Zenodo does not accept",
        {**MINIMAL, "creators": [{"name": "Doe, Jane", "gnd": "(DE-588)118540238"}]},
    ),
    # EDTF rejects a date that is not on the calendar, and Zenodo drops it without a word.
    ("publication date on no calendar", {**MINIMAL, "publication_date": "2024-02-30"}),
    ("publication date with a thirty first of June", {**MINIMAL, "publication_date": "2024-06-31"}),
    (
        "embargo date on no calendar",
        {**MINIMAL, "access_right": "embargoed", "embargo_date": "2027-02-30"},
    ),
    (
        "date range starting on no calendar",
        {**MINIMAL, "dates": [{"type": "collected", "start": "2024-02-30"}]},
    ),
    # `is_isbn` verifies the check digit, which no pattern can, but the shape is worth catching.
    ("imprint isbn that is not an isbn", {**MINIMAL, "imprint_isbn": "1"}),
    # A custom field whose value has the wrong container type is dropped by RDM without a word.
    (
        "custom field holding a string instead of a list",
        {**MINIMAL, "custom": {"dwc:family": "Felidae"}},
    ),
    ("custom field holding a bare number", {**MINIMAL, "custom": {"dwc:decimalLatitude": 51.05}}),
    (
        "custom field holding a string instead of an object",
        {**MINIMAL, "custom": {"thesis:thesis": "Ghent University"}},
    ),
]


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def test_repo_zenodo_json(validator):
    metadata = json.loads((REPO_ROOT / ".zenodo.json").read_text())
    assert list(validator.iter_errors(metadata)) == []


@pytest.mark.parametrize(("label", "metadata"), ACCEPTED, ids=[label for label, _ in ACCEPTED])
def test_accepted(validator, label, metadata):
    errors = [error.message for error in validator.iter_errors(metadata)]
    assert errors == []


@pytest.mark.parametrize(("label", "metadata"), REJECTED, ids=[label for label, _ in REJECTED])
def test_rejected(validator, label, metadata):
    assert list(validator.iter_errors(metadata)) != []
