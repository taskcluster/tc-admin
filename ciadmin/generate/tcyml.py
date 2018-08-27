# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import aiohttp
from asyncio import Lock

from ..util.sessions import aiohttp_session

_cache = {}
_lock = {}


async def get(repo_path, revision='default'):
    '''
    Get `.taskcluster.yml` from 'default' (or the given revision) at the named
    repo_path.  Note that this does not parse the yml (so that it can be hashed
    in its original form).

    If the file is not found, this returns None.
    '''
    with await _lock.setdefault(repo_path, Lock()):
        if repo_path in _cache:
            return _cache[repo_path]

        url = '{}/raw-file/{}/.taskcluster.yml'.format(repo_path, revision)
        try:
            async with aiohttp_session().get(url) as response:
                response.raise_for_status()
                result = await response.read()
        except aiohttp.ClientResponseError as e:
            if e.code == 404:
                result = None
            else:
                raise e

        _cache[repo_path] = result
        return _cache[repo_path]
