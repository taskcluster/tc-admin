# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import blessings

from .appconfig import AppConfig
from .util.ansi import strip_ansi
from .util.sessions import aiohttp_session
from .util.taskcluster import tcClientOptions
from .constants import (
    ACTION_CREATE,
    ACTION_UPDATE,
    ACTION_DELETE,
    BEFORE_APPLY,
    AFTER_APPLY,
)

from taskcluster.aio import Auth, Hooks, WorkerManager, Secrets
from taskcluster import TaskclusterRestFailure

t = blessings.Terminal()


class Updater:
    """
    A simple one-instance class to encapsulate shared Taskcluster API clients.
    """

    @classmethod
    async def setup(cls):
        return cls(await tcClientOptions(), session=aiohttp_session())

    def __init__(self, options, session):
        "Use `Updater.create()` instead of calling this directly."
        self.auth = Auth(options, session)
        self.secrets = Secrets(options, session)
        self.hooks = Hooks(options, session)
        self.worker_manager = WorkerManager(options, session)

    async def create_role(self, role):
        await self.auth.createRole(role.roleId, role.to_api())

    async def update_role(self, role):
        await self.auth.updateRole(role.roleId, role.to_api())

    async def delete_role(self, role):
        await self.auth.deleteRole(role.roleId)

    async def create_client(self, client):
        await self.auth.createClient(client.clientId, client.to_api())

    async def update_client(self, client):
        await self.auth.updateClient(client.clientId, client.to_api())

    async def delete_client(self, client):
        await self.auth.deleteClient(client.clientId)

    async def create_secret(self, secret):
        if not secret.has_secret():
            raise RuntimeError("Cannot apply secrets with --without-secrets")
        await self.secrets.set(secret.name, secret.to_api())

    async def update_secret(self, secret):
        if not secret.has_secret():
            raise RuntimeError("Cannot apply secrets with --without-secrets")
        await self.secrets.set(secret.name, secret.to_api())

    async def delete_secret(self, secret):
        await self.secrets.remove(secret.name)

    async def create_hook(self, hook):
        await self.hooks.createHook(hook.hookGroupId, hook.hookId, hook.to_api())

    async def update_hook(self, hook):
        await self.hooks.updateHook(hook.hookGroupId, hook.hookId, hook.to_api())

    async def delete_hook(self, hook):
        await self.hooks.removeHook(hook.hookGroupId, hook.hookId)

    async def create_workerpool(self, wp):
        try:
            await self.worker_manager.createWorkerPool(wp.workerPoolId, wp.to_api())
        except TaskclusterRestFailure as e:
            # A 409 Conflict error indicates this worker pool already exists,
            # and in most cases this means it's still in the process of being
            # deleted (that is, has providerId = "null-provider" as set by
            # deleteWorkerPool).  In this case, we just update the worker pool
            # in-place.
            if e.status_code == 409:
                return await self.update_workerpool(wp)
            raise

    async def update_workerpool(self, wp):
        await self.worker_manager.updateWorkerPool(wp.workerPoolId, wp.to_api())

    async def delete_workerpool(self, wp):
        await self.worker_manager.deleteWorkerPool(wp.workerPoolId)

    async def update_resource(self, verb, resource):
        # Run callbacks for that resource before the apply
        appconfig = AppConfig.current()
        await appconfig.callbacks.run(BEFORE_APPLY, verb, resource)

        msg = {
            ACTION_CREATE: "{t.green}Creating{t.normal} {resource.id}",
            ACTION_UPDATE: "{t.yellow}Updating{t.normal} {resource.id}",
            ACTION_DELETE: "{t.red}Deleting{t.normal} {resource.id}",
        }[verb].format(t=t, resource=resource)
        try:
            print(msg)
            await getattr(self, "{}_{}".format(verb, resource.kind.lower()))(resource)
        except Exception as e:
            raise RuntimeError("Error While {}".format(strip_ansi(msg))) from e

        # Run callbacks for that resource after the apply
        await appconfig.callbacks.run(AFTER_APPLY, verb, resource)

    async def update(self, generated, current):
        "update all resources to match generated"
        generated_resources = {r.id: r for r in generated}
        current_resources = {r.id: r for r in current}
        all_resources = set(generated_resources) | set(current_resources)

        # Note that we do these updates one at a time.  The Auth service
        # serializes role changes, and it takes quite a while to recalculate
        # for each change.  Kicking off tens or hundreds of updates in parallel
        # would lead to requests timing out waiting for others to complete.  So
        # it's best to just be gentle and do one at a time.

        for id in all_resources:
            if id in generated_resources:
                g = generated_resources[id]
                if id in current_resources:
                    c = current_resources[id]
                    if c == g:
                        continue  # no difference
                    await self.update_resource(ACTION_UPDATE, g)
                else:
                    await self.update_resource(ACTION_CREATE, g)
            else:
                c = current_resources[id]
                await self.update_resource(ACTION_DELETE, c)
