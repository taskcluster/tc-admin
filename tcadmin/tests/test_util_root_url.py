# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import click

from tcadmin.util import root_url as root_url_mod


@pytest.fixture
def root_url():
    # clear the memoization
    root_url_mod._root_url = None
    return root_url_mod.root_url


@pytest.mark.asyncio
async def test_root_url_from_env(appconfig, root_url, monkeypatch):
    monkeypatch.setenv("TASKCLUSTER_ROOT_URL", "https://tc-testing.example.com")
    assert await root_url() == "https://tc-testing.example.com"


@pytest.mark.asyncio
async def test_root_url_not_set(appconfig, root_url, monkeypatch):
    monkeypatch.delenv("TASKCLUSTER_ROOT_URL", raising=False)
    with pytest.raises(click.UsageError):
        await root_url()


@pytest.mark.asyncio
async def test_root_url_from_appconfig_str(appconfig, root_url, monkeypatch):
    monkeypatch.delenv("TASKCLUSTER_ROOT_URL", raising=False)
    appconfig.root_url = "https://tc-testing.example.com"
    assert await root_url() == "https://tc-testing.example.com"


@pytest.mark.asyncio
async def test_root_url_from_appconfig_fn(appconfig, root_url, monkeypatch):
    monkeypatch.delenv("TASKCLUSTER_ROOT_URL", raising=False)

    async def get_root():
        return "https://tc-testing.example.com"

    appconfig.root_url = get_root
    assert await root_url() == "https://tc-testing.example.com"


@pytest.mark.asyncio
async def test_root_url_from_appconfig_diferent(appconfig, root_url, monkeypatch):
    monkeypatch.setenv("TASKCLUSTER_ROOT_URL", "https://tc-testing.example.com")
    appconfig.root_url = "https://something-else.example.com"
    with pytest.raises(click.UsageError):
        await root_url()
