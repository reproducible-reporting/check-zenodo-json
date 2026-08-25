#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: Apache-2.0
# Usage: .github/scripts/extract-notes.sh OWNER/SLUG TAG
# Write the changelog section of TAG to notes.md, for use as GitHub release notes.

set -euo pipefail

REPOSITORY="${1}"
TAG="${2}"
VERSION="${TAG#v}"

# Copy the lines between the heading of this version and the heading of the previous one.
# The oldest version has no heading below it, so the link reference definitions
# at the bottom of the changelog end the section as well.
# Blank lines are buffered and only written out once a non-blank line follows,
# which drops the blank lines at both ends while keeping those in between.
awk -v version="${VERSION}" '
    !found { if (index($0, "## [" version "]") == 1) found = 1; next }
    /^## / || /^\[[^]]*\]: / { exit }
    /^$/ { if (started) blanks++; next }
    { for (; blanks > 0; blanks--) print ""; started = 1; print }
' CHANGELOG.md > notes.md

if [[ ! -s notes.md ]]; then
    echo "No section for version ${VERSION} found in CHANGELOG.md" >&2
    exit 1
fi

# Point at the changelog as it stood at this tag, which also holds the older entries.
CHANGELOG_URL="https://github.com/${REPOSITORY}/blob/${TAG}/CHANGELOG.md"
printf '\nSee [CHANGELOG.md](%s) for the full history.\n' "${CHANGELOG_URL}" >> notes.md
