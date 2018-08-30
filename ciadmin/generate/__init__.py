# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import asyncio

from ..resources import Resources
from . import (
    ciconfig,
    scm_group_roles,
    project_roles,
    in_tree_actions,
    cron_tasks,
    moz_tree,
)
from ..options import decorate


def options(fn):
    return decorate(fn, ciconfig.options)


async def resources():
    '''
    Generate the desired resources
    '''
    resources = Resources()

    # manage a few repo-related prefixes so that any removed repos have their
    # resources deleted
    resources.manage('Role=repo:hg.mozilla.org/incubator/*')
    resources.manage('Role=repo:hg.mozilla.org/releases/*')
    # NOTE: we can't do this with /projects/, because it contains nss and nss-try, which
    # are not confiugred in projects.yml

    await asyncio.gather(
        scm_group_roles.update_resources(resources),
        project_roles.update_resources(resources),
        in_tree_actions.update_resources(resources),
        cron_tasks.update_resources(resources),
        moz_tree.update_resources(resources),
    )
    return resources
