# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import blessings

from .util.ansi import strip_ansi
from .util.sessions import aiohttp_session

from taskcluster.aio import Auth, Hooks, AwsProvisioner, WorkerManager
from taskcluster import optionsFromEnvironment, TaskclusterRestFailure

t = blessings.Terminal()


class Updater:
    """
    A simple one-instance class to encapsulate shared Taskcluster API clients.
    """

    def __init__(self):
        self.auth = Auth(optionsFromEnvironment(), session=aiohttp_session())
        self.hooks = Hooks(optionsFromEnvironment(), session=aiohttp_session())
        self.awsprovisioner = AwsProvisioner(
            optionsFromEnvironment(), session=aiohttp_session()
        )
        self.worker_manager = WorkerManager(
            optionsFromEnvironment(), session=aiohttp_session()
        )

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

    async def create_awsprovisionerworkertype(self, wt):
        await self.awsprovisioner.createWorkerType(wt.workerType, wt.to_api())

    async def update_awsprovisionerworkertype(self, wt):
        await self.awsprovisioner.updateWorkerType(wt.workerType, wt.to_api())

    async def delete_awsprovisionerworkertype(self, wt):
        await self.awsprovisioner.removeWorkerType(wt.workerType)

    async def create_workerpool(self, wp):
        try:
            await self.worker_manager.createWorkerPool(wp.workerPoolId, wp.to_api())
        except TaskclusterRestFailure as e:
            # A 409 Conflict error indicates this worker pool already exists,
            # and in most cases this means it's still in the process of being
            # deleted (that is, has providerId = "null-provider" as set below in
            # delete_workerpool).  In this case, we just update the worker pool
            # in-place.
            if e.status_code == 409:
                return await self.update_workerpool(wp)
            raise

    async def update_workerpool(self, wp):
        await self.worker_manager.updateWorkerPool(wp.workerPoolId, wp.to_api())

    async def delete_workerpool(self, wp):
        # worker-manager doesn't support deleting directly; instead we set the
        # providerId to "null-provider".  Once the pool has no workers, the
        # worker-manager will delete it.
        as_api = wp.to_api()
        as_api["providerId"] = "null-provider"
        await self.worker_manager.updateWorkerPool(wp.workerPoolId, as_api)

    async def update_resource(self, verb, resource):
        msg = {
            "create": "{t.green}Creating{t.normal} {resource.id}",
            "update": "{t.yellow}Updating{t.normal} {resource.id}",
            "delete": "{t.red}Deleting{t.normal} {resource.id}",
        }[verb].format(t=t, resource=resource)
        try:
            print(msg)
            await getattr(self, "{}_{}".format(verb, resource.kind.lower()))(resource)
        except Exception as e:
            raise RuntimeError("Error While {}".format(strip_ansi(msg))) from e

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
                    await self.update_resource("update", g)
                else:
                    await self.update_resource("create", g)
            else:
                c = current_resources[id]
                await self.update_resource("delete", c)
