# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import aiohttp
import functools

_aiohttp_session = None


def aiohttp_session():
    "Return the active aiohttp session"
    return _aiohttp_session


def with_aiohttp_session(fn):
    @functools.wraps(fn)
    async def wrap(*args, **kwargs):
        global _aiohttp_session
        assert not _aiohttp_session, "nested with_aiohttp_session calls!"
        default_headers = {
            "User-Agent": "tc-admin",
        }

        async with aiohttp.ClientSession(headers=default_headers) as session:
            _aiohttp_session = session
            try:
                return await fn(*args, **kwargs)
            finally:
                _aiohttp_session = None

    return wrap
