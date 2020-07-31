# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from tcadmin.resources import Resources, Role
from tcadmin.current.roles import fetch_roles


pytestmark = pytest.mark.usefixtures("appconfig")


@pytest.fixture
def AuthForRoles(mocker):
    """
    Mock out Auth in tcadmin.current.roles.

    The expected return value for listRoles should be set in Auth.roles
    """
    Auth = mocker.patch("tcadmin.current.roles.Auth")
    Auth.roles = []

    class FakeAuth:
        async def listRoles(self):
            return Auth.roles

    Auth.return_value = FakeAuth()
    return Auth


@pytest.fixture
def make_role():
    def make_role(**kwargs):
        kwargs.setdefault("roleId", "test-role")
        kwargs.setdefault("description", "descr")
        kwargs.setdefault("scopes", ["scope-a"])
        return kwargs

    return make_role


@pytest.mark.asyncio
async def test_fetch_roles_empty(AuthForRoles):
    "When there are no roles, nothing happens"
    resources = Resources([], [".*"])
    await fetch_roles(resources)
    assert list(resources) == []


@pytest.mark.asyncio
async def test_fetch_roles_managed(AuthForRoles, make_role):
    "When a role is present and managed, it is included"
    resources = Resources([], [".*"])
    api_role = make_role()
    AuthForRoles.roles.append(api_role)
    await fetch_roles(resources)
    assert list(resources) == [Role.from_api(api_role)]


@pytest.mark.asyncio
async def test_fetch_roles_unmanaged(AuthForRoles, make_role):
    "When a role is present and unmanaged, it is not included"
    resources = Resources([], ["Role=managed*"])
    api_role1 = make_role(roleId="managed-role")
    api_role2 = make_role(roleId="un-managed-role")
    AuthForRoles.roles.extend([api_role1, api_role2])
    await fetch_roles(resources)
    assert list(resources) == [Role.from_api(api_role1)]
