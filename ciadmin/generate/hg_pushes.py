# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import textwrap
import jsone

from ..resources import Role, Hook, Binding
from .ciconfig.projects import Project
from .ciconfig.get import get_ciconfig_file


async def make_hook(project, environment):
    hookGroupId = "hg-push"
    hookId = project.alias

    # use the hg-push-template.yml from the ci-configuration repository, rendering it
    # with the context values described there
    task_template = await get_ciconfig_file("hg-push-template.yml")
    task = jsone.render(
        task_template,
        {
            "level": project.level,
            "trust_domain": project.trust_domain,
            "hookGroupId": hookGroupId,
            "hookId": hookId,
            "project_repo": project.repo,
            "project_role_prefix": project.role_prefix,
            "alias": project.alias,
        },
    )

    return Hook(
        hookGroupId=hookGroupId,
        hookId=hookId,
        name="{}/{}".format(hookGroupId, hookId),
        description=textwrap.dedent(
            """\
            On-push task for repository {}.

            This hook listens to pulse messages from `hg.mozilla.org` and creates a task which
            quickly creates a decision task when such a message arrives.
            """
        ).format(project.repo),
        owner="taskcluster-notifications@mozilla.com",
        emailOnError=False,
        schedule=[],
        bindings=(
            Binding(
                exchange="exchange/hgpushes/v2", routingKeyPattern=project.repo_path
            ),
        ),
        task=task,
        triggerSchema={
            "type": "object",
            "required": ["payload"],
            "properties": {
                "payload": {
                    "type": "object",
                    "description": "Hg push payload - see "
                    "https://mozilla-version-control-tools.readthedocs.io"
                    "/en/latest/hgmo/notifications.html#pulse-notifications.",
                    "required": ["type", "data"],
                    "properties": {
                        "type": {"enum": ["changegroup.1"], "default": "changegroup.1"},
                        "data": {
                            "type": "object",
                            "required": ["repo_url", "heads", "pushlog_pushes"],
                            "properties": {
                                "repo_url": {
                                    "enum": [project.repo],
                                    "default": project.repo,
                                },
                                "heads": {
                                    "type": "array",
                                    # a tuple pattern, limiting this to an array of length exactly 1
                                    "items": [
                                        {"type": "string", "pattern": "^[0-9a-z]{40}$"}
                                    ],
                                },
                                "pushlog_pushes": {
                                    "type": "array",
                                    # a tuple pattern, limiting this to an array of length exactly 1
                                    "items": [
                                        {
                                            "type": "object",
                                            "required": ["time", "pushid", "user"],
                                            "properties": {
                                                "time": {
                                                    "type": "integer",
                                                    "default": 0,
                                                },
                                                "pushid": {
                                                    "type": "integer",
                                                    "default": 0,
                                                },
                                                "user": {
                                                    "type": "string",
                                                    "format": "email",
                                                    "default": "nobody@mozilla.com",
                                                },
                                                # not used by the hook, but allowed here for copy-pasta:
                                                "push_json_url": {"type": "string"},
                                                "push_full_json_url": {
                                                    "type": "string"
                                                },
                                            },
                                            "additionalProperties": False,
                                        }
                                    ],
                                },
                                # not used by this hook, but allowed here for copy-pasta:
                                "source": {},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "additionalProperties": False,
                },
                # not used by this hook, but allowed here for copy-pasta:
                "_meta": {},
            },
            "additionalProperties": False,
        },
    )


async def update_resources(resources, environment):
    """
    Manage the hooks and roles for cron tasks
    """
    projects = await Project.fetch_all()
    projects = [p for p in projects if p.feature("hg-push")]
    trust_domains = set(project.trust_domain for project in projects)

    # manage the hg-push/* hooks, and corresponding roles
    for trust_domain in trust_domains:
        resources.manage("Hook=hg-push/*")
        resources.manage("Role=hook-id:hg-push/*")

    for project in projects:
        hook = await make_hook(project, environment)
        resources.add(hook)

        role = Role(
            roleId="hook-id:{}/{}".format(hook.hookGroupId, hook.hookId),
            description="Scopes associated with hg pushes for project `{}`".format(
                project.alias
            ),
            scopes=[
                "assume:{}:branch:default".format(project.role_prefix),
                # all hg-push tasks use the same workerType, and branches do not have permission
                # to create tasks on that workerType
                "queue:create-task:highest:aws-provisioner-v1/hg-push",
            ],
        )
        resources.add(role)
