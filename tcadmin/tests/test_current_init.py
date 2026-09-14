# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

import tcadmin.current as tc_current
from tcadmin.current import resources as current_resources


@pytest.fixture
def fetchers(mocker):
    "Mock out all of the per-kind fetch functions in `fetch_fns`"
    mocks = {kind: mocker.AsyncMock() for kind in tc_current.fetch_fns}
    mocker.patch.dict(tc_current.fetch_fns, mocks)
    return mocks


@pytest.mark.asyncio
async def test_resources_only_fetches_managed_kinds(fetchers):
    "Only kinds present in `managed` are fetched"
    await current_resources(["Client=(?!mozilla-auth0/).*", "Role=hook-id:.*"])

    fetchers["Client"].assert_called_once()
    fetchers["Role"].assert_called_once()
    fetchers["Hook"].assert_not_called()
    fetchers["WorkerPool"].assert_not_called()
    fetchers["Secret"].assert_not_called()


@pytest.mark.asyncio
async def test_resources_fetches_nothing_when_unmanaged(fetchers):
    "No fetchers run when nothing is managed"
    await current_resources([])

    for fetcher in fetchers.values():
        fetcher.assert_not_called()


@pytest.mark.asyncio
async def test_resources_fetches_all_kinds_when_all_managed(fetchers):
    "All fetchers run when every kind is managed"
    await current_resources(
        ["Client=.*", "Role=.*", "Hook=.*", "WorkerPool=.*", "Secret=.*"]
    )

    for fetcher in fetchers.values():
        fetcher.assert_called_once()


@pytest.mark.asyncio
async def test_resources_honours_fetch_fns_patch(mocker):
    "Replacing an entry in `fetch_fns` (e.g. by a downstream consumer) is honoured"
    fake_fetch_clients = mocker.AsyncMock()
    mocker.patch.dict(tc_current.fetch_fns, {"Client": fake_fetch_clients})

    await current_resources(["Client=.*"])

    fake_fetch_clients.assert_called_once()
