# Pre-commit Hook for Validation of `.zenodo.json` Files

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![License: CC0-1.0](https://img.shields.io/badge/license-CC0--1.0-blue)](LICENSES/CC0-1.0.txt)

When Zenodo archives a GitHub release,
it reads the deposit metadata from a `.zenodo.json` file in the repository.
A deserializer loads that file, silently drops keys it does not recognize
and rejects values outside its controlled vocabularies.
This repository aims to facilitate the creation of `.zenodo.json` files that Zenodo will accept,
by checking your `.zenodo.json` against a JSON Schema locally before you commit it.

This repository provides a [pre-commit](https://pre-commit.com/) hook
that validates `.zenodo.json` against a JSON Schema before the file is committed.

The [GitHub integration section in the Zenodo developer documentation](https://developers.zenodo.org/#github)
refers to [a legacy deposit JSON Schema](https://github.com/zenodo/zenodo/blob/master/zenodo/modules/deposit/jsonschemas/deposits/records/legacyrecord.json)
to validate `.zenodo.json` files.
Unfortunately, it lags behind the actual loader and cannot be reused in other projects
unless they are GPL-2.0 licensed.
This repository provides a public domain schema that is compatible with Zenodo's latest loader,
derived from the InvenioRDM and Zenodo codebases, using Claude Opus 5.
The comment at the top of
[`check_zenodo_json/zenodo-derived-legacy-deposit.schema.json`](check_zenodo_json/zenodo-derived-legacy-deposit.schema.json)
records the commits it was derived from.

## Usage

Add the following to `.pre-commit-config.yaml`:

```yaml
repos:
- repo: https://github.com/reproducible-reporting/check-zenodo-json
  rev: v1.0.0
  hooks:
  - id: check-zenodo-json
```

Replace `rev` with the [latest release](
https://github.com/reproducible-reporting/check-zenodo-json/releases),
or let `pre-commit autoupdate` fill it in.
Then install and run the hook:

```bash
pre-commit install
pre-commit run check-zenodo-json --all-files
```

The hook only runs on files called `.zenodo.json`, in any directory of the repository.
It needs no network access, because the schema is installed together with the hook.

### Options

The hook is a wrapper around
[check-jsonschema](https://github.com/python-jsonschema/check-jsonschema),
so its options can be passed through `args`:

```yaml
  - id: check-zenodo-json
    args: ["--output-format", "json"]
```

The one option it refuses is `--schemafile`.
`check-jsonschema` honours the last one it is given,
so passing your own would quietly validate against something other than the Zenodo schema.

### Without Pre-commit

The validation can also be run as a command,
for example in a continuous integration workflow:

```bash
pip install git+https://github.com/reproducible-reporting/check-zenodo-json
check-zenodo-json .zenodo.json
```

### With Another Validator

The schema is a single self-contained draft-07 document,
so any validator can use it directly:

```bash
SCHEMA_URL=https://raw.githubusercontent.com/reproducible-reporting/check-zenodo-json/main/check_zenodo_json/zenodo-derived-legacy-deposit.schema.json
check-jsonschema --schemafile "$SCHEMA_URL" .zenodo.json
```

Pin a release tag instead of `main` when the exact version of the schema matters.

## Test Your `.zenodo.json` against the Zenodo Sandbox

In addition to using the pre-commit hook,
we recommend that you create an account on the Zenodo sandbox at
[https://sandbox.zenodo.org](https://sandbox.zenodo.org).
Create a personal access token with the `deposit:write` scope in that account,
and you can send your metadata to the sandbox to see what Zenodo makes of it.

Run the command below from the directory that holds `.zenodo.json`,
with [jq](https://jqlang.github.io/jq/) installed:

```bash
curl -s -X POST "https://sandbox.zenodo.org/api/deposit/depositions" \
  -H "Authorization: Bearer YOUR_SANDBOX_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"metadata\": $(cat .zenodo.json)}" \
  -w "%{http_code}" | jq
```

where you replace `YOUR_SANDBOX_TOKEN` with your token.
The last output line shows the HTTP status code of the request:

- **201** means that the deposit was created,
  so every value passed the controlled vocabularies.
- **400** means that the load failed,
  and the response is a JSON error log naming the missing or invalid fields.
- **401** or **403** means that the token is missing, wrong,
  or does not carry the `deposit:write` scope.
  Such a response says nothing about your metadata.
  The reverse does not hold:
  Zenodo validates the metadata before it checks the token,
  so a wrong token still gives you a 400 as long as the metadata is invalid.

A 201 does not mean that Zenodo used everything you wrote,
because the loader drops keys it does not recognize without a word.
That is what the pre-commit hook is for.

The `metadata` object in the response is not the deposit as Zenodo stored it.
It is that deposit translated back into the legacy format,
so it differs from your file in ways that have nothing to do with what survived.
A `license` comes back as whichever legacy identifier maps onto the same InvenioRDM one,
so `mit` returns as `mit-license` and `apache-2.0` as `apache2.0`.
A license that exists only in the legacy vocabulary, such as `gfdl`,
does reach the record but has no legacy identifier to come back as, so it looks dropped.
An `alternate_identifiers` entry comes back under `related_identifiers`.
A `dates` entry with only a `start` comes back without it.

To see what Zenodo actually stored, ask for the record itself:

```bash
curl -s -H "Authorization: Bearer YOUR_SANDBOX_TOKEN" \
  -H "Accept: application/vnd.inveniordm.v1+json" \
  "https://sandbox.zenodo.org/api/records/DEPOSIT_ID/draft" | jq .metadata
```

Each successful request creates a draft deposit in your sandbox account.
Remove it with the `id` from the response:

```bash
curl -s -X DELETE \
  "https://sandbox.zenodo.org/api/deposit/depositions/DEPOSIT_ID" \
  -H "Authorization: Bearer YOUR_SANDBOX_TOKEN"
```

## Scope of the Schema

The schema tries to accept only what Zenodo accepts (or converts to),
based on a static AI analysis of its source code and by probing the Zenodo sandbox.
This has a few important implications:

- **The schema may contain errors.**
  Do not expect AI-generated schema files to be perfect.
  While this repository contains some testing infrastructure,
  there is no exhaustive test suite for the correctness of the schema.
  If you find a case where Zenodo accepts and uses
  a field in `.zenodo.json` that the schema rejects,
  or vice versa, please [open an issue](https://github.com/reproducible-reporting/check-zenodo-json/issues).
- **The schema rejects mistakes, not limitations.**
  The following table shows the policy used to design the schema:

  | What Zenodo does with it | Example | Schema |
  |---|---|---|
  | Reads it into the record | `title`, `license` | Accept |
  | Reads it, then drops it when archiving a release | `communities`, `custom` | Accept |
  | Rejects the value, even where the key is dropped | `access_right: "public"` | Reject |
  | Never reads it, so it has no effect | `type` on a creator | Reject |

  This policy is motivated as follows:

  - **A key that Zenodo ignores (silently) should be an error here.**
    For instance, a `type` on an entry of `creators` is valid according to the Zenodo documentation,
    yet the loader drops it, because creators have no role in InvenioRDM.
    The hook reports it, since a silently ignored key is almost never intended.
  - **Not every key that survives the load reaches the record.**
    When Zenodo archives a GitHub release,
    it keeps only the metadata part of the loaded file.
    The access settings, the custom fields, the communities and the DOI of the deposit
    are built separately,
    so `access_right`, `embargo_date`, `doi`, `communities`, `subjects`, `custom`
    and the journal, conference, imprint and thesis fields
    do not reach a record created from a release.
    The schema still validates them,
    because a wrong value in most of them makes the whole load fail,
    and because a key that quietly does nothing is worth knowing about.

- **A value can be valid without being in the schema.**
  Zenodo extends its vocabularies over time,
  so a license, a relation, or a resource type may have become valid after the schema was derived.
  Please [open an issue](https://github.com/reproducible-reporting/check-zenodo-json/issues)
  when the hook rejects metadata that Zenodo accepts.
- **The schema is derived from a version of Zenodo that can only be bracketed.**
  Zenodo publishes no version endpoint,
  and the InvenioRDM version in the generator meta tag of every page
  is too coarse to name a deployment.
  The schema was derived from `zenodo/zenodo-rdm@6386403`,
  the closest available match to what `zenodo.org` served on 2026-08-25,
  inferred from its frontend build and from two behaviours that changed in known releases.
  The sandbox ran a newer release on that day,
  so a behaviour confirmed there is not by itself proof of what the public site does.
- **A controlled value is written in one canonical spelling.**
  Zenodo lower cases a license, a relation, a contributor role and a date type
  before it looks the value up,
  so it accepts `MIT`, `IsCitedBy` and `Collected`
  just as readily as `mit`, `isCitedBy` and `collected`.
  The schema asks for a single spelling of each:
  the lower case identifier for a license, because that is the form the record carries,
  and the spelling of the Zenodo documentation for the other three.
  The legacy deposit API reports a license differently again,
  as explained in the sandbox section above.
  Note that a license found only in the legacy vocabulary, such as `gfdl`,
  is looked up without that normalization,
  so there Zenodo requires the lower case form as well.
- **Leaving `license` out is a choice Zenodo makes for you.**
  When `access_right` is `open` or `embargoed` and there is no `license`,
  the loader assigns CC-BY-4.0, or CC0-1.0 for a dataset, without a word.
  A release archived from GitHub first tries the license GitHub detected for the repository,
  and falls back to CC-BY-4.0 when there is none.
  A software repository rarely wants either, so it is worth setting `license` explicitly.
- **`access_right: "closed"` is stored as `restricted`.**
  The loader builds the same access settings for both, so the deposit reports the latter.

The schema validates the structure and the vocabularies of the metadata,
and the shape of the identifiers and dates that Zenodo would otherwise discard in silence.
Some things stay out of reach:

- **A check digit is never verified.**
  An ORCID and an ISBN both carry one, and Zenodo does check it.
  A pattern cannot, so the schema only pins down the shape.
  An identifier of the right shape with the wrong check digit still passes the hook.
  Zenodo then drops the ISBN,
  and mangles the ORCID in a way that costs the creator their name in the deposit.
  A GND is the other way round:
  Zenodo checks its shape and nothing else,
  so the schema catches everything Zenodo would refuse,
  and a value outside that shape makes the load fail with a server error rather than a message.
- **A date range is not checked for order,**
  because a JSON Schema pattern cannot compare the two ends.
  Zenodo drops a range that runs backwards.
  A day that does not exist, such as the thirty first of June, is caught,
  but the twenty ninth of February is allowed in every year.
- **The value of a custom field is only checked for its container type,**
  that is whether it should be a list, an object or a single string.
  The 91 custom fields carry as many different value schemas,
  so a value of the right container type but the wrong content passes the hook
  and is then dropped by Zenodo without a word.
- **Existence is never checked.**
  The schema does not know whether an ORCID belongs to anyone,
  whether a DOI resolves,
  or whether a grant or a community is known to Zenodo.

## Development

The development environment is managed with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra dev
```

Run the tests, which pin down what the schema accepts and rejects:

```bash
pytest
```

Run the linters and formatters:

```bash
pre-commit run --all
```

## License

- `check_zenodo_json/zenodo-derived-legacy-deposit.schema.json` is licensed under **CC0-1.0**,
  to make it easily reusable in a project using a different license.
- The rest of the code is licensed under **Apache-2.0**.
