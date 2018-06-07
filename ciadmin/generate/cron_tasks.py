# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import textwrap
import jsone
import re

from ..resources import Role, Hook
from .projects import Project
from . import ciconfig


async def make_hook(project):
    hookGroupId = 'project-releng'
    hookId = 'cron-task-{}'.format(project.hgmo_path.replace('/', '-'))

    # set up some options that differ for comm-central checkouts (which must
    # clone two repositories) and gecko checkouts (which only clone one)
    if not project.gecko_repo:
        # There is no `gecko_repo` for this project, so it is itself a regular gecko source repo
        repo_env = {
            'GECKO_BASE_REPOSITORY': 'https://hg.mozilla.org/mozilla-unified',
            'GECKO_HEAD_REPOSITORY': project.repo,
            'GECKO_HEAD_REF': 'default',
        }
        checkout_options = [
            '--vcs-checkout=/builds/worker/checkouts/gecko',
        ]
        mach_cron_options = ''
    else:
        # This project's configuration points to a separate gecko_repo, and should be checked
        # out as a subdirectory of that repo
        repo_env = {
            'GECKO_BASE_REPOSITORY': 'https://hg.mozilla.org/mozilla-unified',
            'GECKO_HEAD_REPOSITORY': project.gecko_repo,
            'GECKO_HEAD_REF': 'default',
            'COMM_BASE_REPOSITORY': 'https://hg.mozilla.org/comm-central',
            'COMM_HEAD_REPOSITORY': project.repo,
            'COMM_HEAD_REF': 'default',
        }
        checkout_options = [
            '--vcs-checkout=/builds/worker/checkouts/gecko',
            '--comm-checkout=/builds/worker/checkouts/gecko/comm',
        ]
        mach_cron_options = '--root=comm/'

    # use the cron-task-template.yml from the ci-configuration repository, rendering it
    # with the context values described there
    task_template = await ciconfig.get('cron-task-template.yml')
    task = jsone.render(task_template, {
        'level': project.level,
        'hookGroupId': hookGroupId,
        'hookId': hookId,
        'repo_env': repo_env,
        'checkout_options': checkout_options,
        'project_repo': project.repo,
        'alias': project.alias,
        'mach_cron_options': mach_cron_options,
        'trim_whitespace': lambda s: re.sub('\s+', ' ', s).strip(),
    })

    return Hook(
        hookGroupId=hookGroupId,
        hookId=hookId,
        name='{}/{}'.format(hookGroupId, hookId),
        description=textwrap.dedent('''\
            Cron task for repository {}.

            This hook is fired every 15 minutes, creating a task that consults .cron.yml in
            the corresponding repository.
            ''').format(project.repo),
        owner='taskcluster-notifications@mozilla.com',
        emailOnError=True,
        schedule=[
            '0 0,15,30,45 * * * *',  # every 15 minutes
        ],
        task=task,
        # this schema simply requires an empty object (the default)
        triggerSchema={
            'type': 'object',
            'properties': {},
            'additionalProperties': False,
        })


async def update_resources(resources):
    '''
    Manage the hooks and roles for cron tasks
    '''
    projects = await Project.fetch_all()

    # manage the cron-task-* hooks, and corresponding roles; these are all nested under project-releng
    # but should probably move to project-{gecko,comm} someday..
    resources.manage('Hook=project-releng/cron-task-*')
    resources.manage('Role=hook-id:project-releng/cron-task-*')

    for project in projects:
        # if this project does not thave the `taskcluster-cron` feature, it does not get
        # a hook.
        if not project.feature('taskcluster-cron'):
            continue

        hook = await make_hook(project)
        resources.add(hook)

        role = Role(
            roleId='hook-id:{}/{}'.format(hook.hookGroupId, hook.hookId),
            description='Scopes associated with cron tasks for project `{}`'.format(project.alias),
            # this task has the scopes of *all* cron tasks in this project; the tasks it creates will have
            # the scopes for a specific cron task (replacing * with the task name)
            scopes=['assume:repo:hg.mozilla.org/{}:cron:*'.format(project.hgmo_path)])
        resources.add(role)
