# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import textwrap

from tcadmin.resources.resources import Resource
from tcadmin.resources.role import Role


pytestmark = pytest.mark.usefixtures("appconfig")


def test_role_formatter():
    "Roles are properly formatted with a string, including the description preamble and sorted scopes"
    role = Role("my:role-id", "This is my role", ["b", "a", "c"])
    assert str(role) == textwrap.dedent(
        """\
        Role=my:role-id:
          roleId: my:role-id
          description:
            *DO NOT EDIT* - This resource is configured automatically.
            
            This is my role
          scopes:
            - a
            - b
            - c"""  # noqa: E501, W293
    )


def test_role_json():
    "Roles are properly output as JSON, including the description preamble and sorted scopes"
    role = Role("my:role-id", "This is my role", ["b", "a", "c"])
    assert role == Resource.from_json(role.to_json())
    assert role.to_json() == {
        "roleId": "my:role-id",
        "kind": "Role",
        "description": "*DO NOT EDIT* - This resource is configured automatically.\n\nThis is my role",
        "scopes": ["a", "b", "c"],
    }


def test_role_from_api():
    "Roles are properly read from a Taskcluster API result"
    api_result = {
        "roleId": "my:role-id",
        "description": "*DO NOT EDIT* - This resource is configured automatically.\n\nThis is my role",
        "scopes": ["scope-a", "scope-b"],
    }
    role = Role.from_api(api_result)
    assert role.roleId == "my:role-id"
    assert role.description == api_result["description"]
    assert role.scopes == ("scope-a", "scope-b")


def test_role_merge_simple():
    "Roles with matching descriptions can be merged"
    r1 = Role(roleId="role", description="test", scopes=["a"])
    r2 = Role(roleId="role", description="test", scopes=["b"])
    merged = r1.merge(r2)
    assert merged.roleId == "role"
    assert merged.description.endswith("test")
    assert merged.scopes == ("a", "b")


def test_role_merge_normalized():
    "Scopes are normalized when merging"
    r1 = Role(roleId="role", description="test", scopes=["a", "b*"])
    r2 = Role(roleId="role", description="test", scopes=["a", "bcdef", "c*"])
    merged = r1.merge(r2)
    assert merged.roleId == "role"
    assert merged.description.endswith("test")
    assert merged.scopes == ("a", "b*", "c*")


def test_role_merge_different_descr():
    "When both sides have a description, the left (self) side wins"
    r1 = Role(roleId="role", description="test1", scopes=["a"])
    r2 = Role(roleId="role", description="test2", scopes=["b"])
    merged = r1.merge(r2)
    assert merged.description.endswith("test1")
    assert merged.scopes == ("a", "b")


def test_role_merge_missing_description_uses_other_side():
    "If only one side has a description, that description is used"
    with_descr = Role(roleId="role", description="test", scopes=["a"])
    without_descr = Role(roleId="role", scopes=["b"])

    merged = without_descr.merge(with_descr)
    assert merged.description.endswith("test")
    assert merged.scopes == ("a", "b")

    merged = with_descr.merge(without_descr)
    assert merged.description.endswith("test")
    assert merged.scopes == ("a", "b")


def test_role_merge_neither_has_description(appconfig):
    "If neither side has a description, the merged role has none either"
    r1 = Role(roleId="role", scopes=["a"])
    r2 = Role(roleId="role", scopes=["b"])
    merged = r1.merge(r2)
    assert merged.description == appconfig.description_prefix
    assert merged.scopes == ("a", "b")


def test_role_description_is_optional(appconfig):
    "A role can be constructed without a description at all"
    role = Role(roleId="role", scopes=["a"])
    assert role.description == appconfig.description_prefix
