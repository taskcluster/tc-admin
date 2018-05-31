# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import hashlib
import textwrap
import yaml
import datetime
import iso8601
from taskcluster.async import Hooks

from ..resources import Role, Hook
from .projects import Project
from . import tcyml
from .actions import Action
from ..util import (
    aiohttp_session,
    MatchList,
)

# Any existing hooks that no longer correspond to active .taskcluster.yml files
# will nonetheless be kept around until this time has passed since they were
# last fired.  This ensures that any "popular" hooks stick around, for example
# to support try jobs run against old revisions.
HOOK_RETENTION_TIME = datetime.timedelta(days=60)


async def hash_taskcluster_ymls():
    '''
    Download and hash .taskcluster.yml from every project repository
    '''
    projects = await Project.fetch_all()
    tcyml_projects = [p for p in projects if p.feature(
        'taskcluster-push') or p.feature('taskcluster-cron')]
    tcymls = await asyncio.gather(*(tcyml.get(p.repo) for p in tcyml_projects))

    # hash the value of this .taskcluster.yml.  Note that this must match the
    # hashing in gecko:taskcluster/taskgraph/actions/registry.py
    def hash(val):
        return hashlib.sha256(val).hexdigest()[:10]

    rv = {}
    for tcy in tcymls:
        # some ancient projects have no .taskcluster.yml
        if not tcy:
            continue

        # some old projects have .taskcluster.yml's that are not valid YAML (back in the day,
        # mozilla-taskcluster used mustache to templatize the text before parsing it..). Ignore
        # those projects.
        try:
            parsed = yaml.load(tcy)
        except Exception:
            continue

        # some slightly less old projects have {tasks: $let: .., in: [..]} instead of
        # the expected {tasks: [{$let: .., in: ..}]}.  Those can be ignored too.
        if not isinstance(parsed['tasks'], list):
            continue
        rv[hash(tcy)] = parsed
    return rv


def make_hook(action, tcyml_content, tcyml_hash):
    hookGroupId = 'project-{}'.format(action.trust_domain)
    hookId = 'in-tree-action-{}-{}/{}'.format(action.level, action.action_perm, tcyml_hash)

    # schema-generation utilities

    def obj(_description=None, **properties):
        schema = {
            'type': 'object',
            'additionalProperties': False,
            'required': list(properties.keys()),
            'properties': properties,
        }
        if _description:
            schema['description'] = _description
        return schema

    def prop(description, type='string', **extra):
        return dict(description=description, type=type, **extra)

    # The triggerSchema describes the input to the hook.  This is provided by the hookPayload
    # template in the actions.json file generated in-tree, and is divided nicely into
    # information from the decision task and information about the user's action request.
    trigger_schema = obj(textwrap.dedent(
        '''Information required to trigger this hook.  This is provided by the `hookPayload`
        template in the `actions.json` file generated in-tree.'''),
        decision=obj(textwrap.dedent(
            '''Information provided by the decision task; this is usually baked into
            `actions.json`, although any value could be supplied in a direct call to
            `hooks.triggerHook`.'''),
            action=obj(
                'Information about the action to perform',
                name=prop('action name'),
                title=prop('action title'),
                description=prop('action description'),
                taskGroupId=prop('taskGroupId of the decision task'),
                cb_name=prop('name of the in-tree callback function'),
                symbol=prop('treeherder symbol')),
            push=obj(
                'Information about the push that created the decision task',
                owner=prop('user who made the original push'),
                revision=prop('revision of the original push'),
                pushlog_id=prop('Mercurial pushlog ID of the original push')),
            repository=obj(
                'Information about the repository where the push occurred',
                url=prop('repository URL (without trailing slash)', pattern='[^/]$'),
                project=prop('repository project name (also known as "alias")'),
                level=prop('repository SCM level')),
            parameters={
                'type': 'object',
                'description': 'decision task parameters',
                'additionalProperties': True,
        }),
        user=obj(
            'Information provided by the user or user interface',
            # TODO: provide input schema for action
            input={
                'anyOf': [
                    {'type': 'object', 'description': 'user input for the task'},
                    {'const': None, 'description': 'null when the action takes no input'},
                ]
            },
            taskId={
                'anyOf': [
                    prop('taskId of the task on which this action was activated'),
                    {'const': None, 'description': 'null when the action is activated for a taskGroup'},
                ]
            },
            taskGroupId=prop('taskGroupId on which this task was activated'),
    ),
    )

    # Given a JSON-e context value `payload` matching the above trigger schema,
    # as well as the `taskId` provided by the hooks service (giving the taskId
    # of the new task), the following JSON-e template rearranges the provided
    # values and supplies them as context to an embedded `.taskclsuter.yml`.
    # This context format is what `.taskcluster.yml` expects, and is based on
    # that provided by mozilla-taskcluster.

    task = {
        '$let': {
            'tasks_for': 'action',
            'action': {
                'name': '${payload.decision.action.name}',
                'title': '${payload.decision.action.title}',
                'description': '${payload.decision.action.description}',
                'taskGroupId': '${payload.decision.action.taskGroupId}',
                'symbol': '${payload.decision.action.symbol}',

                # Calculated repo_scope.  This is based on user input (the repository),
                # but the hooks service checks that this is satisfied by the
                # `hook-id:<hookGroupId>/<hookId>` role, which is set up above to only
                # contain scopes for repositories at this level. Note that the
                # action_perm is *not* based on user input, but is fixed in the
                # hookPayload template.  We would like to get rid of this parameter and
                # calculate it directly in .taskcluster.yml, once all the other work
                # for actions-as-hooks has finished
                'repo_scope': 'assume:repo:${payload.decision.repository.url[8:]}:action:' + action.action_perm,

                # cb_name is user-specified for generic actions, but not for those with their own action_perm
                'cb_name':
                '${payload.decision.action.cb_name}' if action.action_perm == 'generic' else action.action_perm,
            },

            # remaining sections are copied en masse from the hook payload
            'push': {'$eval': 'payload.decision.push'},
            'repository': {'$eval': 'payload.decision.repository'},
            'input': {'$eval': 'payload.user.input'},
            'parameters': {'$eval': 'payload.decision.parameters'},

            # taskId and taskGroupId represent the task and/or task group the user has targetted
            # with this action
            'taskId': {'$eval': 'payload.user.taskId'},
            'taskGroupId': {'$eval': 'payload.user.taskGroupId'},

            # the hooks service provides the taskId that it will use for the resulting action task
            'ownTaskId': {'$eval': 'taskId'},
        },
        'in': tcyml_content['tasks'][0],
    }

    return Hook(
        hookGroupId=hookGroupId,
        hookId=hookId,
        name='{}/{}'.format(hookGroupId, hookId),
        description=textwrap.dedent('''\
            Action task {} at level {}, with `.taskcluster.yml` hash {}.

            This hook is fired in response to actions defined in a Gecko decision task's `actions.json`.
            ''').format(action.action_perm, action.level, tcyml_hash),
        owner='taskcluster-notifications@mozilla.com',
        emailOnError=True,
        schedule=[],
        task=task,
        triggerSchema=trigger_schema)


async def update_resources(resources):
    '''
    Manage the resources related to in-tree actions.
    '''
    await asyncio.gather(
        update_action_hook_resources(resources),
        update_action_access_resources(resources),
    )


async def update_action_hook_resources(resources):
    '''
    Manage the hooks and accompanying roles for in-tree actions.
    '''
    hashed_tcymls = await hash_taskcluster_ymls()
    actions = await Action.fetch_all()
    projects = await Project.fetch_all()

    # manage the in-tree-action-* hooks, and corresponding roles, for each trust domain
    trust_domains = set(action.trust_domain for action in actions)
    for trust_domain in trust_domains:
        resources.manage('Hook=project-{}/in-tree-action-*'.format(trust_domain))
        resources.manage('Role=hook-id:project-{}/in-tree-action-*'.format(trust_domain))

    projects_by_level = {l: [p for p in projects if p.level == l] for l in (1, 2, 3)}

    # generate the hooks themselves and corresponding hook-id roles
    added_hooks = set()
    for action in actions:
        for tcyml_hash, tcyml_content in hashed_tcymls.items():
            hook = make_hook(action, tcyml_content, tcyml_hash)
            resources.add(hook)
            added_hooks.add(hook.id)

        # use a single, star-suffixed role for all hashed versions of a hook
        role = Role(
            roleId='hook-id:project-{}/in-tree-action-{}-{}/*'.format(
                action.trust_domain, action.level, action.action_perm),
            description='Scopes associated with {} action `{}` on each repo at level {}'.format(
                action.trust_domain, action.action_perm, action.level),
            scopes=[
                'assume:repo:hg.mozilla.org/{}:action:{}'.format(p.hgmo_path, action.action_perm)
                for p in projects_by_level[action.level]])
        resources.add(role)

    # download all existing hooks and check the last time they were used
    hooks = Hooks(session=aiohttp_session())
    interesting = MatchList(
        'Hook=project-{}/in-tree-action-*'.format(trust_domain)
        for trust_domain in trust_domains)
    for trust_domain in trust_domains:
        hookGroupId = 'project-{}'.format(trust_domain)
        for hook in (await hooks.listHooks(hookGroupId))['hooks']:
            hook = Hook.from_api(hook)
            # ignore if this is not an in-tree-action hook
            if not interesting.matches(hook.id):
                continue

            # ignore if we've already generated this hook
            if hook.id in added_hooks:
                continue

            # ignore if the hook has never been fired
            hookStatus = await hooks.getHookStatus(hook.hookGroupId, hook.hookId)
            if 'lastFire' not in hookStatus or 'time' not in hookStatus['lastFire']:
                continue

            # ignore if it's too old; do the arithmetic in days to avoid timezone issues
            last = iso8601.parse_date(hookStatus['lastFire']['time'])
            age = datetime.date.today() - last.date()
            if age > HOOK_RETENTION_TIME:
                continue

            # we want to keep this hook, so we add it to the "generated"
            # resources, ensuring it does not get deleted.
            if 'for historical purposes' not in hook.description:
                description = hook.description + \
                    '\n\nThis hook is no longer current and is kept for historical purposes.'
                hook = hook.evolve(description=description)
            resources.add(hook)


async def update_action_access_resources(resources):
    '''
    Manage the project-<domain>:in-tree-action-trigger:<group> roles.  These
    roles are assumed by `mozilla-group:<group> and give users in that group
    access to trigger specific hooks.
    '''

    actions = await Action.fetch_all()

    # Each action can be described as a hook (well, a hookId with a * matching the hash), and
    # each action lists the groups that should have access to it.  So this just performs a little
    # transform to get the set of actions each group has access to, and then encodes those as
    # roles.

    trust_domains = set(action.trust_domain for action in actions)
    for trust_domain in trust_domains:
        resources.manage('Role=project:{}:in-tree-action-trigger:*'.format(trust_domain))

    roles = {}
    for action in actions:
        scope = 'hooks:trigger-hook:project-{}/in-tree-action-{}-{}/*'.format(
                action.trust_domain, action.level, action.action_perm)
        for group in action.groups:
            roleId = 'project:{}:in-tree-action-trigger:{}'.format(action.trust_domain, group)
            roles.setdefault(roleId, (group, []))[1].append(scope)

    for roleId, (group, scopes) in roles.items():
        description = 'Permission for people in the {} group to trigger action hooks'.format(group)
        role = Role(
            roleId=roleId,
            description=description,
            scopes=scopes)
        resources.add(role)
