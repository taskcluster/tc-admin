# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
import attr
from typing import NamedTuple


class Match(NamedTuple):
    include: str
    excludes: tuple[str, ...] = ()


def make_entries(patterns):
    entries = []
    for p in patterns:
        if isinstance(p, Match):
            entries.append(Match(p.include, tuple(p.excludes)))
        elif isinstance(p, dict):
            entries.append(Match(p["include"], tuple(p.get("excludes", ()))))
        else:
            entries.append(Match(p, ()))
    return entries


@attr.s
class MatchList:
    """
    A MatchList is a list of regular expressions that can determine whether a
    given string matches one of those patterns.  Patterns are rooted at the
    left, but should use `$` where required to match the end of the string.

    Each pattern is stored as a `Match(include, excludes)` pair: `excludes` are
    checked against the same string, from the same starting position, as
    `include` itself -- they are not relative to wherever `include` matched.
    """

    _entries = attr.ib(type=list, converter=make_entries)

    def add(self, include, excludes=()):
        "Add `include` to the set of patterns, optionally carving out `excludes`."
        self._entries.append(Match(include, tuple(excludes)))

    def extend(self, other):
        "Fold another MatchList's patterns (and their excludes) into this one."
        self._entries.extend(other._entries)

    def __iter__(self):
        return iter(self._entries)

    def __str__(self):
        lines = []
        for entry in self._entries:
            lines.append("- " + entry.include)
            if entry.excludes:
                lines.append("  Excluding:")
                lines.extend("    - " + exclude for exclude in entry.excludes)
        return "\n".join(lines)

    def matches(self, item):
        "Return True if this item is matched by one of the patterns in the list"
        return any(
            re.match(entry.include, item)
            and not any(re.match(exclude, item) for exclude in entry.excludes)
            for entry in self._entries
        )

    def to_json(self):
        "Convert to a JSON-able data structure, preserving excludes"
        return [
            {"include": entry.include, "excludes": list(entry.excludes)}
            if entry.excludes
            else entry.include
            for entry in self._entries
        ]
