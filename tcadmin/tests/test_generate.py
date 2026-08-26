# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest

from tcadmin import generate
from tcadmin.appconfig import AppConfig
from tcadmin.options import test_options
from tcadmin.resources import Resources, Role


@pytest.mark.asyncio
async def test_resources_generates_no_path_given():
    "With no --generated path, resources() calls the registered generators"
    called = []

    async def add_a_role(resources):
        called.append(True)
        resources.manage("Role=.*")
        resources.add(Role(roleId="r", description="d", scopes=[]))

    appconfig = AppConfig()
    appconfig.generators.register(add_a_role)

    with AppConfig._as_current(appconfig):
        with test_options(generated=None):
            resources = await generate.resources()

    assert called == [True]
    assert [r.id for r in resources] == ["Role=r"]


@pytest.mark.asyncio
async def test_resources_loads_from_path_without_generating(tmp_path):
    "With --generated, resources() loads the file and skips the generators"
    called = []

    async def add_a_role(resources):
        called.append(True)

    appconfig = AppConfig()
    appconfig.generators.register(add_a_role)

    path = tmp_path / "generated.json"

    with AppConfig._as_current(appconfig):
        saved = Resources([Role(roleId="r", description="d", scopes=[])], ["Role=.*"])
        path.write_text(json.dumps(saved.to_json()))

        with test_options(generated=str(path)):
            resources = await generate.resources()

    assert called == []
    assert [r.id for r in resources] == ["Role=r"]
    assert list(resources.managed) == ["Role=.*"]
