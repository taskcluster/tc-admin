# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from ciadmin.generate.ciconfig.projects import Project
from ciadmin.util.scopes import satisfies


async def project_scopes(resolver, level):
    projects = await Project.fetch_all()
    scopes = ["assume:mozilla-group:active_scm_level_{}".format(level)]
    for project in projects:
        if project.level == level:
            scopes.append("assume:{}:*".format(project.role_prefix))
    return resolver.expandScopes(scopes)


@pytest.fixture(scope="module")
async def l1_scopes(generated_resolver):
    return await project_scopes(generated_resolver, level=1)


@pytest.fixture(scope="module")
async def l3_scopes(generated_resolver):
    return await project_scopes(generated_resolver, level=3)


@pytest.mark.parametrize(
    "scope,present",
    [
        # try (level 1) gets dep-signing, but nothing else
        ("project:comm:thunderbird:releng:signing:cert:dep-signing", True),
        ("project:comm:thunderbird:releng:signing:cert:nightly-signing", False),
        ("project:comm:thunderbird:releng:signing:cert:release-signing", False),
        ("project:releng:signing:cert:dep-signing", True),
        ("project:releng:signing:cert:nightly-signing", False),
        ("project:releng:signing:cert:release-signing", False),
        ("queue:create-task:highest:scriptworker-prov-v1/depsigning", False),
        ("queue:create-task:highest:scriptworker-prov-v1/signing-linux-v1", False),
        ("queue:create-task:highest:scriptworker-prov-v1/tb-depsigning", False),
        ("queue:create-task:highest:scriptworker-prov-v1/tb-signing-v1", False),
    ],
)
def check_l1_scopes(l1_scopes, scope, present):
    if present:
        assert satisfies(l1_scopes, [scope])
    else:
        assert not satisfies(l1_scopes, [scope])


@pytest.mark.parametrize(
    "scope,present",
    [
        # level 3 gets all kinds of signing
        ("project:comm:thunderbird:releng:signing:cert:dep-signing", True),
        # 'project:comm:thunderbird:releng:signing:cert:nightly-signing' is not configured yet..
        ("project:comm:thunderbird:releng:signing:cert:release-signing", True),
        ("project:releng:signing:cert:dep-signing", True),
        ("project:releng:signing:cert:nightly-signing", True),
        ("project:releng:signing:cert:release-signing", True),
        ("queue:create-task:highest:scriptworker-prov-v1/depsigning", True),
        ("queue:create-task:highest:scriptworker-prov-v1/signing-linux-v1", True),
        ("queue:create-task:highest:scriptworker-prov-v1/tb-depsigning", True),
        ("queue:create-task:highest:scriptworker-prov-v1/tb-signing-v1", True),
    ],
)
def check_l3_scopes(l3_scopes, scope, present):
    if present:
        assert satisfies(l3_scopes, [scope])
    else:
        assert not satisfies(l3_scopes, [scope])
