# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from ciadmin.generate.ciconfig.environments import Environment


@pytest.mark.asyncio
async def test_fetch_empty(mock_ciconfig_file):
    mock_ciconfig_file("environments.yml", {})
    assert await Environment.fetch_all() == []


@pytest.mark.asyncio
async def test_fetch_entry(mock_ciconfig_file):
    mock_ciconfig_file(
        "environments.yml", {"dev": {"root_url": "https://tc-tests.localhost"}}
    )
    assert await Environment.fetch_all() == [
        Environment(
            environment="dev",
            root_url="https://tc-tests.localhost",
            modify_resources=[],
        )
    ]


@pytest.mark.asyncio
async def test_fetch_entry_with_mods(mock_ciconfig_file):
    mock_ciconfig_file(
        "environments.yml",
        {
            "dev": {
                "root_url": "https://tc-tests.localhost",
                "modify_resources": ["mod1", "mod2"],
            }
        },
    )
    assert await Environment.fetch_all() == [
        Environment(
            environment="dev",
            root_url="https://tc-tests.localhost",
            modify_resources=["mod1", "mod2"],
        )
    ]
