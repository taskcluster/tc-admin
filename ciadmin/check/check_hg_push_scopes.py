# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from tcadmin.util.scopes import satisfies
from tcadmin.resources import Hook, Role


@pytest.fixture(scope="module")
def ci_group_roles(generated, generated_resolver):
    """
    A dictionary mapping ci-group roles (project:releng:ci-group:..) to their expanded scopes
    """
    return {
        resource.roleId: generated_resolver.expandScopes(["assume:" + resource.roleId])
        for resource in generated
        if isinstance(resource, Role)
        and resource.roleId.startswith("project:releng:ci-group:")
    }


@pytest.fixture(scope="module")
def hg_push_hooks(generated):
    """
    A list of hookId for all hg-push hooks (all of them with hookGroupid `hg-push`
    """
    return [
        resource.hookId
        for resource in generated
        if isinstance(resource, Hook) and resource.hookGroupId == "hg-push"
    ]


@pytest.fixture(scope="module")
def repo_roles(generated, generated_resolver):
    """
    A dictionary mapping repository roles (repo::..) to their expanded scopes
    """
    return {
        resource.roleId: generated_resolver.expandScopes(["assume:" + resource.roleId])
        for resource in generated
        if isinstance(resource, Role) and resource.roleId.startswith("repo:")
    }


@pytest.fixture(scope="module")
def create_task_scopes(queue_priorities):
    """
    All scopes that could allow creating a task on the hg-push workerType
    """
    return [
        "queue:create-task:{}:aws-provisioner-v1/hg-push".format(priority)
        for priority in queue_priorities
    ] + ["queue:create-task:aws-provisioner-v1/hg-push"]


def test_ci_groups_create_task(ci_group_roles, create_task_scopes):
    """
    Verify that no ci-groups have permission to create tasks on the hg-push workertype
    """
    for roleId, role_scopes in ci_group_roles.items():
        for queue_scope in create_task_scopes:
            assert not satisfies(role_scopes, [queue_scope])


def test_repos_create_task(repo_roles, create_task_scopes):
    """
    Verify that no project repos have permission to create tasks on the hg-push
    workertype -- only the hooks should have that permission
    """
    for roleId, role_scopes in repo_roles.items():
        for queue_scope in create_task_scopes:
            assert not satisfies(role_scopes, [queue_scope])


def test_ci_groups_trigger_hook(ci_group_roles, hg_push_hooks):
    """
    Verify that no ci-groups have permission to trigger hg-push hooks
    """
    for roleId, role_scopes in ci_group_roles.items():
        for hookId in hg_push_hooks:
            hook_scope = "hooks:trigger-hook:hg-push/" + hookId
            assert not satisfies(role_scopes, [hook_scope])
