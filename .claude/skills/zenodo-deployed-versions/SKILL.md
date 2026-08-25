---
name: zenodo-deployed-versions
description: >-
  How to determine which InvenioRDM and zenodo-rdm versions
  zenodo.org and sandbox.zenodo.org are running,
  and the dated observations behind the current schema's provenance.
  Use before re-deriving or re-verifying the schema against upstream.
---

# Deployed Versions

Zenodo publishes no version endpoint,
so the version of the software behind `zenodo.org` and `sandbox.zenodo.org`
has to be read off the pages and the assets they serve.
Everything in this section is an observation made on a given day, not a standing fact.

Every HTML page carries `<meta name="generator" content="InvenioRDM 15.0"/>`.
The value is not hardcoded:
`invenio-app-rdm` sets `THEME_GENERATOR` from `importlib.metadata.version("invenio-app-rdm")`
truncated to major and minor, and `invenio-theme` renders it in `invenio_theme/page.html`,
so it names the package that is actually installed.
It cannot separate the `15.0.0bN.devM` pre-releases Zenodo currently pins.
On 2026-08-25 both `zenodo.org` and `sandbox.zenodo.org` reported `InvenioRDM 15.0`.

The `zenodo-rdm` version is not exposed at all and has to be inferred from the built frontend.
The bundler runtime at `/static/dist/js/manifest.<hash>.js` gives it away.
A runtime containing `rspackChunkinvenio_assets` is a build at or after
the `feat(assets): switch to pnpm and rspack` commit of 2026-08-24,
and a webpack runtime with twenty character content hashes is older than that commit.
On 2026-08-25 `sandbox.zenodo.org` served an rspack build whose assets were dated
2026-08-24 15:08 UTC, less than an hour after the `v26.1.0` tag,
while `zenodo.org` served a webpack build, which puts it at `v25.2.5` or earlier.

Two publicly visible behaviours bracketed `zenodo.org` from below on that same day.
Its EU community page rendered the help link as `https://help.zenodo.org/guides/eu/`,
a spelling that `templates/themes/horizon/invenio_app_rdm/footer.html` first carried in `v25.1.0`.
Its legacy serialization of a record funded by an award that has a DOI,
requested with `Accept: application/vnd.zenodo.v1+json`,
returned the grant with `"doi": "10.3030/101135472"` rather than failing,
and the `KeyError` that would have failed it was fixed in `v25.2.2`.
So `zenodo.org` ran something between `v25.2.2` and `v25.2.5` on 2026-08-25.

The schema was derived from `zenodo/zenodo-rdm@6386403`,
which is `v25.2.5` plus one commit that touches only `scripts/deploy.py`.
That commit is the best available stand-in for what `zenodo.org` was running,
and nothing the schema depends on moves inside the bracket below it.
`v25.2.2` and `v25.2.5` pin different `invenio-rdm-records` revisions, 33.3.0 against 35.0.0,
but that range touches no file under `invenio_rdm_records/contrib`
and none of the GitHub release code,
and `zenodo-rdm` itself changes nothing under `site/zenodo_rdm/legacy`,
nothing in `site/zenodo_rdm/custom_fields`
and nothing in the license data under `legacy/zenodo_legacy`.

Vocabulary fixtures are not reloaded when Zenodo deploys.
`v25.2.4` added a `description` to the award entries in `app_data/vocabularies/awards.yaml`,
yet on 2026-08-25 `https://zenodo.org/api/awards/00k4n6c32::283595` and its sandbox counterpart
both still lacked that field and both reported an `updated` of 2026-08-03.
This is a second reason for reading a vocabulary from the running instance:
the fixture in the repository can be ahead of what the instance serves.
