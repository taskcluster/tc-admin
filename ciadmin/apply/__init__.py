# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
import click
import blessings
from taskcluster.aio import (
    Auth,
    Hooks,
)

from ..util.ansi import strip_ansi
from ..util.sessions import aiohttp_session
from ..resources import Resources
from ..options import decorate, with_click_options

t = blessings.Terminal()


def options(fn):
    return decorate(
        fn,
        click.option('--grep', help='regular expression limiting resources displayed'))


class Modifier:
    '''
    A simple one-instance class to encapsulate shared Taskcluster API clients.
    '''

    def __init__(self):
        self.auth = Auth(session=aiohttp_session())
        self.hooks = Hooks(session=aiohttp_session())

    async def create_role(self, role):
        await self.auth.createRole(role.roleId, role.to_api())

    async def update_role(self, role):
        await self.auth.updateRole(role.roleId, role.to_api())

    async def delete_role(self, role):
        await self.auth.deleteRole(role.roleId)

    async def create_hook(self, hook):
        await self.hooks.createHook(hook.hookGroupId, hook.hookId, hook.to_api())

    async def update_hook(self, hook):
        await self.hooks.updateHook(hook.hookGroupId, hook.hookId, hook.to_api())

    async def delete_hook(self, hook):
        await self.hooks.removeHook(hook.hookGroupId, hook.hookId)

    async def modify_resource(self, verb, resource):
        msg = {
            'create': '{t.green}Creating{t.normal} {resource.id}',
            'update': '{t.yellow}Updating{t.normal} {resource.id}',
            'delete': '{t.red}Deleting{t.normal} {resource.id}',
        }[verb].format(t=t, resource=resource)
        try:
            print(msg)
            await getattr(self, '{}_{}'.format(verb, resource.kind.lower()))(resource)
        except Exception as e:
            raise RuntimeError('Error While {}'.format(strip_ansi(msg))) from e

    async def modify(self, generated, current):
        'modify all resources to match generated'
        generated_resources = {r.id: r for r in generated}
        current_resources = {r.id: r for r in current}
        all_resources = set(generated_resources) | set(current_resources)

        # Note that we do these modifications one at a time.  The Auth service
        # serializes role changes, and it takes quite a while to recalculate
        # for each change.  Kicking off tens or hundreds of modifications in
        # parallel would lead to requests timing out waiting for others to
        # complete.  So it's best to just be gentle and do one at a time.

        for id in all_resources:
            if id in generated_resources:
                g = generated_resources[id]
                if id in current_resources:
                    c = current_resources[id]
                    if c == g:
                        continue  # no difference
                    await self.modify_resource('update', g)
                else:
                    await self.modify_resource('create', g)
            else:
                c = current_resources[id]
                await self.modify_resource('delete', c)


@with_click_options('grep')
async def apply_changes(generated, current, grep):
    # limit the resources considered if --grep
    if grep:
        reg = re.compile(grep)
        generated = Resources(
            managed=generated.managed,
            resources=(r for r in generated.resources if reg.search(r.id)))
        current = Resources(
            managed=current.managed,
            resources=(r for r in current.resources if reg.search(r.id)))

    modifier = Modifier()
    await modifier.modify(generated, current)
