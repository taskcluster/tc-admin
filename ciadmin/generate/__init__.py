# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import asyncio
import os
import click

from ..resources import Resources
from . import (
    ciconfig,
    modify,
    scm_group_roles,
    in_tree_actions,
    cron_tasks,
    hg_pushes,
    grants,
)
from .ciconfig.environments import Environment
from ..options import decorate, with_click_options


def options(fn):
    fn = decorate(fn, ciconfig.options)
    return decorate(
        fn,
        click.option(
            "--environment",
            required=True,
            help="environment for which resources are to be generated",
        ),
    )


@with_click_options("environment")
async def load_environment(environment):
    """
    Load environment.yml and return the instance corresponding to this environment.

    This also sanity-checks the TASKCLUSTER_ROOT_URL
    """
    for env in await Environment.fetch_all():
        if env.environment == environment:
            break
    else:
        raise KeyError("Environment {} is not defined".format(environment))

    # sanity-check, to prevent applying to the wrong Taskcluster instance
    root_url = os.environ.get("TASKCLUSTER_ROOT_URL")
    if root_url and root_url != env.root_url:
        raise RuntimeError(
            "Environment {} expects rootUrl {}, but active credentials are for {}".format(
                environment, env.root_url, root_url
            )
        )

    return env


async def resources():
    """
    Generate the desired resources
    """
    resources = Resources()

    environment = await load_environment()

    await asyncio.gather(
        scm_group_roles.update_resources(resources, environment),
        in_tree_actions.update_resources(resources, environment),
        cron_tasks.update_resources(resources, environment),
        hg_pushes.update_resources(resources, environment),
        grants.update_resources(resources, environment),
    )

    resources = await modify.modify_resources(resources, environment)

    return resources
