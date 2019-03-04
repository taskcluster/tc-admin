# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import asyncio

from ciadmin import current
from ciadmin import generate
from ciadmin.util.sessions import with_aiohttp_session
from ciadmin.util.scopes import Resolver


# Imported from pytest-asyncio, but with scope session
# https://github.com/pytest-dev/pytest-asyncio/issues/75
@pytest.yield_fixture(scope="session")
def event_loop(request):
    """Create an instance of the default event loop for each test run."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
@with_aiohttp_session
async def generated():
    """Return the generated resources"""
    return await generate.resources()


@pytest.fixture(scope="session")
@with_aiohttp_session
async def actual(generated):
    """Return the actual resources (as fetched from Taskcluster)"""
    return await current.resources(generated.managed)


@pytest.fixture(scope="session")
def generated_resolver(generated):
    return Resolver.from_resources(generated)


@pytest.fixture(scope="session")
def queue_priorities():
    return "highest very-high high medium low very-low lowest normal".split()
