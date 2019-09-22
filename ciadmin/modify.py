# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os

from tcadmin.appconfig import AppConfig
from tcadmin.util.root_url import root_url

from ciadmin.environment import Environment
from ciadmin.generate.ciconfig.get import get_ciconfig_file

MODIFIERS = {}


def modifier(fn):
    MODIFIERS[fn.__name__] = fn
    return fn


@modifier
def remove_hook_schedules(resources):
    """
    Remove schedules from all managed hooks, so that they do not run and create tasks.
    """

    def modify(resource):
        if resource.kind != "Hook":
            return resource
        if not resource.schedule:
            return resource
        return resource.evolve(schedule=[])

    return resources.map(modify)


@modifier
def remove_hook_bindings(resources):
    """
    Remove bindings from all managed hooks, so that they do not try to listen
    to exchanges that do not exist.
    """

    def modify(resource):
        if resource.kind != "Hook":
            return resource
        if not resource.bindings:
            return resource
        return resource.evolve(bindings=[])

    return resources.map(modify)


async def modify_resources(resources):
    """
    Apply any `modify_resources` functions to the given resources, as determined
    by the ciconfig `environments.yml` file, and return a new set of resources.
    """
    env_option = AppConfig.current().options.get("--environment")
    environments = await get_ciconfig_file("environments.yml")

    environment = None
    for environment_name, info in environments.items():
        if environment_name == env_option:
            environment = Environment(environment_name, **info)
            break
    else:
        raise KeyError("Environment {} is not defined".format(env_option))

    # sanity-check, to prevent applying to the wrong Taskcluster instance
    if root_url() != environment.root_url:
        raise RuntimeError(
            "Environment {} expects rootUrl {}, but active credentials are for {}".format(
                env_option, environment.root_url, root_url()
            )
        )

    for mod in environment.modify_resources:
        if mod not in MODIFIERS:
            raise KeyError("No modify_resources function named {}".format(mod))
        resources = MODIFIERS[mod](resources)
    return resources
