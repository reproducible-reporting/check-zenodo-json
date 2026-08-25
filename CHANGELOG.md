# Changelog

All notable changes to `check-zenodo-json` are documented on this page.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Effort-based Versioning](https://jacobtomlinson.dev/effver/).

## [Unreleased][]

(no changes yet)

## [1.1.1][] - 2026-08-25

### Fixed

- Corrected the note describing the license of the deposit.

## [1.1.0][] - 2026-08-25

### Added

- The value of every custom field in `custom` is validated,
  not just its container type.
  The `code:programmingLanguage` and `code:developmentStatus` identifiers
  are checked against the vocabularies Zenodo has deployed.
- `conference_url` is checked for being a URL that Zenodo accepts,
  which it already was for `meeting:meeting.url`.

## [1.0.0][] - 2026-08-25

Initial release of `check-zenodo-json`.

[1.0.0]: https://github.com/reproducible-reporting/check-zenodo-json/releases/tag/v1.0.0
[1.1.0]: https://github.com/reproducible-reporting/check-zenodo-json/releases/tag/v1.1.0
[1.1.1]: https://github.com/reproducible-reporting/check-zenodo-json/releases/tag/v1.1.1
