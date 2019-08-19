# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import textwrap
import jsone
import re

from ..resources import Role, Hook
from .ciconfig.projects import Project
from .ciconfig.get import get_ciconfig_file


async def _make_gecko_context(project, environment):
    # set up some options that differ for comm-central checkouts (which must
    # clone two repositories) and gecko checkouts (which only clone one)
    task_template = await get_ciconfig_file("gecko-cron-task-template.yml")

    if not project.parent_repo:
        # There is no `parent_repo` for this project, so it is itself a regular gecko source repo
        context = {
            "repo_env": {
                "GECKO_BASE_REPOSITORY": "https://hg.mozilla.org/mozilla-unified",
                "GECKO_HEAD_REPOSITORY": project.repo,
                "GECKO_HEAD_REF": "default",
            },
            "checkout_options": ["--vcs-checkout=/builds/worker/checkouts/gecko"],
            "cron_options": "",
        }
    else:
        # This project's configuration points to a separate parent_repo, and should be checked
        # out as a subdirectory of that repo
        context = {
            "repo_env": {
                "GECKO_BASE_REPOSITORY": "https://hg.mozilla.org/mozilla-unified",
                "GECKO_HEAD_REPOSITORY": project.parent_repo,
                "GECKO_HEAD_REF": "default",
                "COMM_BASE_REPOSITORY": "https://hg.mozilla.org/comm-central",
                "COMM_HEAD_REPOSITORY": project.repo,
                "COMM_HEAD_REF": "default",
            },
            "checkout_options": [
                "--vcs-checkout=/builds/worker/checkouts/gecko",
                "--comm-checkout=/builds/worker/checkouts/gecko/comm",
            ],
            "cron_options": "--root=comm/",
        }

    return task_template, context


async def _make_taskgraph_context(project, environment):
    task_template = await get_ciconfig_file("taskgraph-cron-task-template.yml")
    context = {
        "repo_env": {
            "VCS_HEAD_REPOSITORY": project.repo,
            "VCS_HEAD_REF": "default" if project.repo_type == "hg" else "master",
            "VCS_REPOSITORY_TYPE": project.repo_type,
        },
        "checkout_options": ["--vcs-checkout=/builds/worker/checkouts/src"],
        "cron_options": "",
    }
    return task_template, context


async def make_hooks(project, environment):
    hookGroupId = "project-releng"
    hookId = "cron-task-{}".format(project.repo_path.replace("/", "-"))

    context = {
        "level": project.level,
        "trust_domain": project.trust_domain,
        "hookGroupId": hookGroupId,
        "hookId": hookId,
        "taskcluster_root_url": environment.root_url,
        "project_repo": project.repo,
        "alias": project.alias,
        "trim_whitespace": lambda s: re.sub(r"\s+", " ", s).strip(),
    }

    if project.feature("gecko-cron"):
        task_template, extra_context = await _make_gecko_context(project, environment)
    elif project.feature("taskgraph-cron"):
        task_template, extra_context = await _make_taskgraph_context(
            project, environment
        )
    else:
        raise Exception("Unknown cron task type.")

    # use the cron-task-template.yml from the ci-configuration repository, rendering it
    # with the context values described there
    context.update(extra_context)
    task = jsone.render(task_template, context)

    resources = [
        Hook(
            hookGroupId=hookGroupId,
            hookId=hookId,
            name="{}/{}".format(hookGroupId, hookId),
            description=textwrap.dedent(
                """\
            Cron task for repository {}.

            This hook is fired every 15 minutes, creating a task that consults .cron.yml in
            the corresponding repository.
            """
            ).format(project.repo),
            owner="taskcluster-notifications@mozilla.com",
            emailOnError=True,
            schedule=["0 0,15,30,45 * * * *"],  # every 15 minutes
            bindings=[],
            task=task,
            # this schema simply requires an empty object (the default)
            triggerSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
        Role(
            roleId="hook-id:{}/{}".format(hookGroupId, hookId),
            description="Scopes associated with cron tasks for project `{}`".format(
                project.alias
            ),
            # this task has the scopes of *all* cron tasks in this project; the tasks it creates will have
            # the scopes for a specific cron task (replacing * with the task name)
            scopes=["assume:{}:cron:*".format(project.role_prefix)],
        ),
    ]

    for cron_target in project.cron_targets:
        target_context = context.copy()
        target_context["cron_options"] += " --force-run={}".format(cron_target)
        target_context["hookId"] = "{}/{}".format(hookId, cron_target)
        task = jsone.render(task_template, target_context)
        resources.extend(
            [
                Hook(
                    hookGroupId=hookGroupId,
                    hookId="{}/{}".format(hookId, cron_target),
                    name="{}/{}/{}".format(hookGroupId, hookId, cron_target),
                    description="""FIXME""",
                    owner="taskcluster-notifications@mozilla.com",
                    emailOnError=True,
                    schedule=[],
                    bindings=[],
                    task=task,
                    # this schema simply requires an empty object (the default)
                    triggerSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                Role(
                    roleId="hook-id:{}/{}/{}".format(hookGroupId, hookId, cron_target),
                    description="Scopes associated with cron tasks for project `{}`".format(
                        project.alias
                    ),
                    scopes=[
                        "assume:{}:cron:{}".format(project.role_prefix, cron_target)
                    ],
                ),
            ]
        )

    return resources


async def update_resources(resources, environment):
    """
    Manage the hooks and roles for cron tasks
    """
    projects = await Project.fetch_all()

    # manage the cron-task-* hooks, and corresponding roles; these are all nested under project-releng
    # but should probably move to project-{gecko,comm} someday..
    resources.manage("Hook=project-releng/cron-task-*")
    resources.manage("Role=hook-id:project-releng/cron-task-*")

    for project in projects:
        # if this project does not thave the `gecko-cron` feature, it does not get
        # a hook.
        if not project.feature("gecko-cron") and not project.feature("taskgraph-cron"):
            continue

        resources.update(await make_hooks(project, environment))
