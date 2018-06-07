# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import functools
import aiohttp
import attr
import json

_aiohttp_session = None


def pretty_json(value):
    return json.dumps(value, sort_keys=True, indent=4, separators=(',', ': '))


def aiohttp_session():
    'Return the active aiohttp session'
    return _aiohttp_session


def with_aiohttp_session(fn):
    @functools.wraps(fn)
    async def wrap(*args, **kwargs):
        global _aiohttp_session
        assert not _aiohttp_session, 'nested with_aiohttp_session calls!'
        with aiohttp.ClientSession() as session:
            _aiohttp_session = session
            try:
                await fn(*args, **kwargs)
            finally:
                _aiohttp_session = None
    return wrap


@attr.s
class MatchList:
    '''
    A sorted list of patterns.  If you're familiar with Taskcluster scopes and
    scopesets, this is the same thing.

    Each pattern matches itself and, if it ends in '*', any string ending with
    the remainder of the pattern before the '*'.

    A MatchList is a list of patterns that automatically keeps itself
    "minimized" such that no pattern matches any other pattern.

    Emtpy strings are prohibited.
    '''

    _patterns = attr.ib(type=list)

    def __attrs_post_init__(self):
        self._minimize()

    def add(self, item):
        'Add `item` to the set of patterns'
        if not self.matches(item):
            self._patterns.append(item)
            self._minimize()

    def matches(self, item):
        'Return True if this item is matched by one of the patterns in the list'
        return any(item.startswith(pat[:-1]) if pat[-1] == '*' else item == pat for pat in self)

    def __iter__(self):
        return self._patterns.__iter__()

    def _minimize(self):
        # this is O(n^2) but we don't manage 1000's of items, so it's OK for now
        patterns = set(self._patterns)  # remove duplicates
        if '' in patterns:
            raise RuntimeError('Empty strings are not allowed in MatchList')
        self._patterns = sorted(
            p1 for p1 in patterns if
            all(p1 == p2 or not (p2.endswith('*') and p1.startswith(p2[:-1])) for p2 in patterns))
