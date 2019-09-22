# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
import attr


def make_regular_expressions(patterns):
    return [re.compile(p) for p in patterns]


@attr.s
class MatchList:
    """
    A MatchList is a list of regular expressions that can determine whether a
    given string matches one of those patterns.  Patterns are rooted at the
    left, but should use `$` where required to match the end of the string.
    """

    _patterns = attr.ib(type=list, converter=make_regular_expressions)

    def add(self, expr):
        "Add `expr` to the set of patterns"
        self._patterns.append(re.compile(expr))

    def __iter__(self):
        return (p.pattern for p in self._patterns)

    def matches(self, item):
        "Return True if this item is matched by one of the patterns in the list"
        return any(pat.match(item) for pat in self._patterns)
