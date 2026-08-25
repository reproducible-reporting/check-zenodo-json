# CLAUDE.md

## Overview

This repository packages a [pre-commit](https://pre-commit.com/) hook, `check-zenodo-json`,
that validates `.zenodo.json` files against a JSON Schema.
Zenodo reads such a file from a GitHub repository when it archives a release,
and it silently ignores keys and values it does not understand,
so mistakes in the metadata surface only after the deposit has been created.
The hook catches them at commit time instead.

`check_zenodo_json/zenodo-derived-legacy-deposit.schema.json` is the schema itself,
a draft-07 document that is also the deliverable of this repository.
It is unofficial, because Zenodo publishes no schema for `.zenodo.json`.
It was derived from the loader that Zenodo actually runs,
`zenodo_rdm.legacy.deserializers`,
with the license vocabulary taken from `zenodo-rdm`
and the resource type, contributor role, relation type and date type vocabularies
read from the running Zenodo instance.
The `$comment` at the top of the schema records where each part came from.

The repository validates its own `.zenodo.json` with the upstream `check-jsonschema` hook,
because a repository cannot use a hook it defines itself.

`LICENSE` and `LICENSES/Apache-2.0.txt` hold the same text on purpose:
the first is the file GitHub looks for, the second is the file REUSE looks for.
They must stay byte-identical, and nothing checks that for you.

## Deployed Versions

Zenodo publishes no version endpoint,
so the version of the software behind `zenodo.org` and `sandbox.zenodo.org`
has to be read off the pages and the assets they serve.
See the `zenodo-deployed-versions` skill for how this was done
and what was observed on 2026-08-25.

## Non-Negotiables

The schema describes what Zenodo does, not what Zenodo documents or what would be convenient.

- **Every change to the schema is backed by the upstream source.**
  A key, a value, or a constraint is added or removed
  because `zenodo_rdm.legacy.deserializers` or a vocabulary Zenodo runs on says so,
  and the `$comment` at the top of the schema is updated with what was consulted.
  Never loosen the schema to make one project's `.zenodo.json` pass.
- **A vocabulary is read from the running Zenodo instance, not from `invenio-rdm-records`.**
  `zenodo-rdm` overrides only some vocabularies in `app_data/vocabularies.yaml`,
  namely licenses, description types, affiliations, funders and awards.
  It inherits the rest from whichever `invenio-rdm-records` fixture its instance was built with,
  and that fixture is not re-synchronised when entries are added upstream,
  so `invenio-rdm-records` on its main branch lists values Zenodo will reject.
  The resource type, contributor role, relation type, date type,
  programming language and development status vocabularies
  therefore come from `https://zenodo.org/api/vocabularies/<name>`,
  which `zenodo.org` and `sandbox.zenodo.org` answer identically.
  The `datacite` property of an entry gives the spelling the Zenodo documentation uses,
  except where DataCite has no equivalent and the property collapses onto another value,
  as it does for `annotator`.
- **A claim about Zenodo's behaviour is tested against the sandbox before it is written down.**
  Post the metadata to `https://sandbox.zenodo.org/api/deposit/depositions`
  and read the record back with `Accept: application/vnd.inveniordm.v1+json`,
  because the legacy response is a translation and differs from what was stored.
  Delete the draft afterwards.
- **Every change to the schema comes with a test.**
  Add the case to `ACCEPTED` or `REJECTED` in `tests/test_zenodo_schema.py`,
  with a comment naming the upstream behaviour that justifies it
  whenever that behaviour is surprising.
- **Input that Zenodo would silently ignore is rejected.**
  The top level keeps `additionalProperties: false`,
  and so does every object inside it,
  because a key that Zenodo drops without a word is exactly the mistake this hook exists to catch.
  The keys of `custom` are no exception:
  they are enumerated from the custom field definitions
  in `zenodo_rdm.custom_fields` and `invenio_rdm_records.contrib`,
  and each one carries the value schema of the marshmallow field it is defined with.
- **A deliberate narrowing is written down where it is made.**
  Zenodo lower cases a license, a relation, a contributor role and a date type
  before it looks the value up,
  so it accepts any capitalisation of the four.
  The schema asks for one canonical spelling of each:
  the lower case identifier for a license, because that is the form the deposit carries,
  and the spelling of the Zenodo documentation for the other three.
  A narrowing like this belongs in the property description, in `README.md`,
  and in `REJECTED` with a comment saying what Zenodo would have accepted.
  Do not extend the rule by analogy.
  A language code, for instance, is not narrowed at all:
  Zenodo never lower cases it, so an upper case code is simply invalid.
  An ORCID is not narrowed either:
  Zenodo accepts the hyphenated form, the bare digits and an `orcid.org` URL,
  and the schema accepts all three.
- **The schema stays draft-07.**
  That is the dialect `check-jsonschema` and the tests validate against.
- **The schema stays a single self-contained file** without external references,
  because it is also consumed directly by URL.

## Development

### Environment

The development environment is managed with [uv](https://docs.astral.sh/uv/), not with `pip`.
Reinstall the development version with:

```bash
uv sync --extra dev
```

This is only needed for running the tests with `pytest`.

### Pre-commit

Pre-commit hooks run automatically on commit.
After making code changes, run `pre-commit run --all` before considering the work done.

The same hooks run in continuous integration on [pre-commit.ci](https://pre-commit.ci/),
which is why the GitHub Actions workflow runs `pytest` and nothing else.
Do not add a linting step to `.github/workflows/`.

## Coding Conventions

### Semantic Line Breaks

All English text in this repo is wrapped using **semantic line breaks**:
break after sentences or logical units, not at a fixed character count.
This covers comments (including SQL comments), docstrings,
Markdown documentation, commit messages, and so on.
See <https://sembr.org/>.
Prose diffs then stay small, because editing one sentence never reflows its neighbours.

- **Every sentence starts on a new line.**
- **Break inside a sentence only where a break is needed, and then at a clause boundary.**
  A sentence that fits within the 100-character line length stays on a single line.
  A longer one is broken before a conjunction or a relative pronoun
  ("and", "but", "because", "which", "if", ...),
  or after a leading subordinate clause.
- **Not every comma is a break.**
  Enumerated items, appositions and short parentheticals stay on the line they started on.

The 100-character line length is a hard cap, not a target to fill.
An extra break inside a long sentence is fine when it clarifies the structure,
but a sentence that already fits on one line is left alone.

### Avoid En and Em Dashes

Write sentences without en or em dashes.
They should never be used in any prose (code comments, docstrings, Markdown, ...),
neither in their UTF-8 glyph form (–, —) nor in ASCII form (--, ---).
Subclauses should be made explicit (e.g. "which", "because", "that")
or split into separate sentences.

### Prose That Ages Well

Stale prose is worse than no prose. When writing comments, docstrings, or other prose, avoid:

- **Describing callers.** Don't note how other code uses a function or class.
  That's the caller's concern, and the remark silently rots when the caller changes.
- **Describing history.** Don't explain what the code used to do or how it changed.
  The current code should speak for itself; history belongs in commit messages.
- **Implementation details in docstrings.** Document the contract (how to use something),
  not how it works internally.
- **Line-number references.** They break as soon as the file changes.
  Point to a function, class, or file name instead.
- **Restating the code.** A comment should say something the code doesn't already say
  (the reason, the invariant, the non-obvious constraint) not paraphrase the next line.
  A purely redundant comment isn't wrong, so nothing forces it to be updated,
  and it drifts out of sync silently.
- **Repetitive and duplicate comments.**
  If a remark is repeated in multiple places, it will rot in one place when updated in another.
  Factor out the common remark into a single function or class docstring, or a Markdown file in `docs/`.
- **Timeless phrasing for point-in-time claims.** An empirical observation about an external
  tool or environment (e.g. "SQLite's planner never picks this index") can stop being true
  after a version upgrade, with nothing to flag the comment as outdated.
  Say what was observed and, when it matters, on what
  (e.g. "as of SQLite 3.45, measured separately").

### Linting (ruff)

Do not add `# noqa` comments unless the violation is a genuine false positive that cannot
be resolved by restructuring the code,
because the project's rule set already excludes rules that would fire spuriously
in this codebase.

### Docstrings

Use **NumPy-style** sections (`Parameters`, `Returns`, `Raises`, ...)
Some conventions specific to this codebase:

- Docstrings are written in Markdown, not reStructuredText! Some important gotcha's:
  - Do not use italics for parameter names, return values, or exception names.
    Use single backticks instead.
  - Use single backticks for all inline code, not double backticks.
  - Use triple backticks for code blocks,
    and specify the language for syntax highlighting (e.g., ```python).
- Lines are wrapped using semantic breaks, per [Semantic Line Breaks](#semantic-line-breaks) above.
- Use the imperative mood for function descriptions
  (e.g., "Compute the hash of a file."),
  except for `@property` getters where the description should be a noun phrase
  (e.g., "The parent directory path.").
- Do not repeat type annotations in the docstring,
  because they are already in the function signature.
- In `Parameters` sections, use the **parameter name** as the heading for each parameter.
  Grouping closely related parameters under a combined heading
  (e.g., `stdout, stderr`) is allowed when parameters are better described together.
- In `Returns` sections, use a **semantic name** for the return value, not the type,
  as these are already in the function signature.

  ```python
  # correct
  Returns
  -------
  parent
      The parent directory path.

  # wrong, because the type is already in the signature
  Returns
  -------
  Path
      The parent directory path.
  ```

### Markdown

Section headings (`##`, `###`, ...) use **Title Case**
(capitalize nouns, verbs, adjectives, and adverbs; lowercase articles,
coordinating conjunctions, and prepositions regardless of length, e.g. "from", "with").
Inline code spans (e.g. `` `run()` ``) keep their own casing and are never title-cased.
