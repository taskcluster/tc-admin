# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os.path
import pytest

from tcadmin.util.sessions import with_aiohttp_session
from ciadmin.generate.ciconfig.get import _read_file

# pin a revision of ci/ci-configuration so we know what to expect
PINNED_REV = "8c90613a29f5"


@pytest.mark.asyncio
@with_aiohttp_session
async def test_get_yml():
    res = await _read_file(
        "projects.yml",
        repository="https://hg.mozilla.org/ci/ci-configuration",
        revision=PINNED_REV,
        directory=None,
    )
    assert res["ash"]["repo"] == "https://hg.mozilla.org/projects/ash"


@pytest.mark.asyncio
@with_aiohttp_session
async def test_get_data():
    res = await _read_file(
        "README.md",
        repository="https://hg.mozilla.org/ci/ci-configuration",
        revision=PINNED_REV,
        directory=None,
    )
    assert b"CI Configuration" in res


@pytest.mark.asyncio
@with_aiohttp_session
async def test_get_file_path():
    res = await _read_file(
        os.path.basename(__file__),
        repository="https://hg.mozilla.org/ci/ci-configuration",
        revision=PINNED_REV,
        directory=os.path.dirname(__file__),
    )
    assert b"self-matching string, hey cool" in res
