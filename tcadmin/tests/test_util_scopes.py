# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import taskcluster
import os

from tcadmin.util.scopes import Resolver, satisfies
from tcadmin.util.taskcluster import optionsFromEnvironment
from tcadmin.resources import Role, Resources


pytestmark = pytest.mark.usefixtures("appconfig")


def test_from_resources():
    resources = Resources(
        resources=[
            Role(roleId="role1", description="1", scopes=["one"]),
            Role(roleId="role2", description="2", scopes=["two"]),
        ],
        managed=["Role=role*"],
    )
    res = Resolver.from_resources(resources)
    assert sorted(res.expandScopes(["assume:role1"])) == ["assume:role1", "one"]


def check_resolved(res, given, expected):
    assert sorted(res.expandScopes(given)) == sorted(expected)


def test_identity():
    res = Resolver({})
    check_resolved(res, ["aa", "bb"], ["aa", "bb"])


def test_expand_simple():
    res = Resolver({"role1": ["r1a", "r1b"]})
    check_resolved(res, ["aa", "assume:role1"], ["aa", "assume:role1", "r1a", "r1b"])


def test_expand_star():
    res = Resolver({"role1": ["r1a", "r1b"], "role2": ["r2a", "r2b"]})
    check_resolved(
        res, ["aa", "assume:role*"], ["aa", "assume:role*", "r1a", "r1b", "r2a", "r2b"]
    )


def test_expand_role_star():
    res = Resolver({"role*": ["rstar"], "role2": ["r2a", "r2b"]})
    check_resolved(
        res, ["aa", "assume:role2"], ["aa", "assume:role2", "rstar", "r2a", "r2b"]
    )


def test_assume_thing_star():
    res = Resolver({"thing-id:*": ["test-scope-1"]})
    check_resolved(
        res, ["assume:thing-id:test"], ["assume:thing-id:test", "test-scope-1"]
    )


def test_assume_can_get_star():
    res = Resolver({"thing-id:*": ["*"]})
    check_resolved(res, ["assume:thing-id:test"], ["*"])


def test_indirect_roles():
    res = Resolver(
        {"test-client-1": ["assume:test-role"], "test-role": ["special-scope"]}
    )
    check_resolved(
        res,
        ["assume:test-client-1"],
        ["assume:test-client-1", "assume:test-role", "special-scope"],
    )


def test_many_indirect_roles():
    roles = {
        "test-role-{}".format(n): ["assume:test-role-{}".format(n + 1)]
        for n in range(1, 10)
    }
    roles["test-role-10"] = ["special-scope"]
    res = Resolver(roles)
    check_resolved(
        res,
        ["assume:test-role-1"],
        ["assume:test-role-{}".format(n) for n in range(1, 11)] + ["special-scope"],
    )


def test_cyclic_roles():
    res = Resolver(
        {
            "test-client-1": ["assume:test-role"],
            "test-role": ["special-scope", "assume:test-client-1"],
        }
    )
    check_resolved(
        res,
        ["assume:test-client-1"],
        ["assume:test-client-1", "assume:test-role", "special-scope"],
    )


def test_astar_means_assume():
    res = Resolver({"test-1": ["a*"], "foo": ["bar"]})
    check_resolved(res, ["assume:test-1"], ["a*", "bar"])


def test_assumestar_means_assume():
    res = Resolver({"test-1": ["assume*"], "foo": ["bar"]})
    check_resolved(res, ["assume:test-1"], ["assume*", "bar"])


def test_parameterized_simple_claim_task():
    res = Resolver({"worker-type:*": ["queue:claim-task:<..>"]})
    check_resolved(
        res,
        ["assume:worker-type:prov1/wt2"],
        ["assume:worker-type:prov1/wt2", "queue:claim-task:prov1/wt2"],
    )
    check_resolved(
        res,
        ["assume:worker-type:prov1/*"],
        ["assume:worker-type:prov1/*", "queue:claim-task:prov1/*"],
    )


def test_parameterized_project_admin():
    res = Resolver(
        {
            "project-admin:*": [
                "auth:create-client:project/<..>/*",
                "assume:project:<..>:*",
                "assume:hook-id:project-<..>/*",
            ]
        }
    )
    check_resolved(
        res,
        ["assume:project-admin:pocket"],
        [
            "assume:hook-id:project-pocket/*",
            "assume:project-admin:pocket",
            "assume:project:pocket:*",
            "auth:create-client:project/pocket/*",
        ],
    )


def test_parameterized_scope_escalation():
    res = Resolver(
        {
            "project:taskcluster:docs-upload:*": [
                "auth:aws-s3:read-write:tc-metadata-<..>/docs"
            ]
        }
    )
    check_resolved(
        res,
        ["assume:project:taskcluster:docs-upload:queue"],
        [
            "assume:project:taskcluster:docs-upload:queue",
            "auth:aws-s3:read-write:tc-metadata-queue/docs",  # looks good..
        ],
    )

    check_resolved(
        res,
        ["assume:project:taskcluster:docs-upload:*"],
        [
            "assume:project:taskcluster:docs-upload:*",
            "auth:aws-s3:read-write:tc-metadata-*",  # SURPRISE!
        ],
    )


def test_parameterized_star_in_replacement():
    res = Resolver({"A*": ["assume:B<..>C"]})
    check_resolved(res, ["assume:Abc*"], ["assume:Abc*", "assume:Bbc*"])


def test_expand_star_in_initial_scopes():
    res = Resolver(
        {
            "repo:hg.mozilla.org/comm-central:cron:nightly-*": [
                "assume:project:comm:thunderbird:comm:releng:nightly:level-3:comm-central"
            ],
            "project:comm:thunderbird:comm:releng:nightly:level-3:comm-central": [
                "comm-stuff"
            ],
        }
    )
    check_resolved(
        res,
        ["assume:repo:hg.mozilla.org/comm-central:cron:*"],
        [
            "assume:repo:hg.mozilla.org/comm-central:cron:*",
            "assume:project:comm:thunderbird:comm:releng:nightly:level-3:comm-central",
            "comm-stuff",
        ],
    )


def test_normalizeScopes_with_stars():
    res = Resolver({})
    check_resolved(
        res,
        [
            "assume:hook-id:garbage/*",
            "assume:hook-id:project-*",
            "assume:hook-id:project-<..>/*",
            "assume:hook-id:project-releng/services-master-*",
            "assume:hook-id:project-releng/services-production-*",
            "assume:hook-id:project-releng/services-testing-*",
            "assume:hook-id:tc-hooks-tests/tc-test-hook",
        ],
        [
            "assume:hook-id:garbage/*",
            "assume:hook-id:project-*",
            "assume:hook-id:tc-hooks-tests/tc-test-hook",
        ],
    )


@pytest.fixture(scope="module")
def auth():
    # tests using this fixture need *some* auth service, but it actually
    # doesn't matter which one
    if "TASKCLUSTER_ROOT_URL" not in os.environ:
        msg = "TASKCLUSTER_ROOT_URL not set"
        if "NO_TEST_SKIP" in os.environ:
            pytest.fail(msg)
        else:
            pytest.skip(msg)
    return taskcluster.Auth(optionsFromEnvironment())


@pytest.fixture(scope="module")
def resolver(auth):
    roles = auth.listRoles()
    return Resolver({r["roleId"]: r["scopes"] for r in roles})


@pytest.mark.slow
@pytest.mark.parametrize(
    "scope",
    [
        "secrets:get:/*",
        "assume:everybody",
        "assume:mozilla-group:focus_android_eng",
        "assume:project-admin:*",
        "assume:project-admin:comm",
        "assume:repo:hg.mozilla.org/comm-central:cron:*",
    ],
)
def test_real_scopes(scope, resolver, auth):
    local = sorted(resolver.expandScopes([scope]))
    real = sorted(auth.expandScopes({"scopes": [scope]})["scopes"])
    assert local == real


def test_satisfies_simple():
    assert satisfies(["scope1", "scope2"], ["scope1"])
    assert not satisfies(["scope1"], ["scope1", "scope2"])


def test_satisfies_stars():
    assert satisfies(["scope:*", "other:*"], ["scope:xyz"])
    assert satisfies(["scope:*", "other:*"], ["scope:"])
    assert not satisfies(["scope:*", "other:*"], ["scope"])
