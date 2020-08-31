# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
from collections import namedtuple
from .constants import BEFORE_APPLY, AFTER_APPLY, ACTIONS
from .resources import Role, Hook, WorkerPool, Client, Secret


Callback = namedtuple("Callback", "callable, actions, resources")
SUPPORTED_RESOURCES = (Role, Hook, WorkerPool, Client, Secret)


class CallbacksRegistry:
    """A named registry collects (async) callbacks for a specific action
    during the apply workflow.
    """

    def __init__(self):
        self.callbacks = {BEFORE_APPLY: [], AFTER_APPLY: []}

    def add(self, trigger, callable, actions=ACTIONS, resources=SUPPORTED_RESOURCES):
        """Store a new async function as a callback that will be triggered during the apply workflow

        * before_apply will trigger the callback before any change is made
        * after_apply will trigger the callback after any change is made

        Supported actions are : create, update, and delete.
        By default all actions are used.

        Supported resources are: Role, Hook, WorkerPool, Client & Secret
        By default all resources are used.

        A callback should have the following signature:

        async def mycallback(action, resource):
            ...

        If a resource matches your requirements, the callback will be triggered with the associated action
        """
        assert trigger in self.callbacks, "{} is not a supported trigger".format(
            trigger
        )
        assert all(
            action in ACTIONS for action in actions
        ), "Some actions are not supported"
        assert all(
            resource in SUPPORTED_RESOURCES for resource in resources
        ), "Some resources are not supported"

        callback = Callback(callable, actions, resources)
        self.callbacks[trigger].append(callback)
        return callback

    async def run(self, trigger, action, resource):
        """Internal helper to run callbacks for a specific trigger, action and resource"""
        assert trigger in self.callbacks, "Invalid trigger {}".format(trigger)

        for callback in self.callbacks[trigger]:
            if action in callback.actions and resource.__class__ in callback.resources:
                await callback.callable(action, resource)
