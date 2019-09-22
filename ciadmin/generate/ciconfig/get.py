# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os
import yaml
from asyncio import Lock

from tcadmin.util.sessions import aiohttp_session
from tcadmin.appconfig import AppConfig

_cache = {}
_lock = {}


async def _read_file(filename, **test_kwargs):
    def opt(n):
        if test_kwargs:
            return test_kwargs[n]
        return AppConfig.current().options.get("--ci-configuration-" + n)

    repository = opt("repository")
    revision = opt("revision")
    directory = opt("directory")

    if directory:
        with open(os.path.join(directory, filename), "rb") as f:
            result = f.read()
    else:
        url = "{}/raw-file/{}/{}".format(
            repository.rstrip("/"), revision, filename.lstrip("/")
        )
        async with aiohttp_session().get(url) as response:
            response.raise_for_status()
            result = await response.read()

    if filename.endswith(".yml"):
        result = yaml.load(result)

    return result


async def get_ciconfig_file(filename):
    """
    Get the named file from the ci-configuration repository, parsing .yml if necessary.

    Fetches are cached, so it's safe to call this many times for the same file.
    """
    with await _lock.setdefault(filename, Lock()):
        if filename in _cache:
            return _cache[filename]

        _cache[filename] = await _read_file(filename)
        return _cache[filename]
