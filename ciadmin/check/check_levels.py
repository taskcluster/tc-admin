# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest

from ciadmin.generate.ciconfig.projects import Project
from ciadmin.util.sessions import with_aiohttp_session, aiohttp_session


async def get_repo_owner(repo):
    session = aiohttp_session()
    async with session.get("{}/json-repoinfo".format(repo)) as response:
        response.raise_for_status()
        result = await response.read()
    owner = json.loads(result)["group_owner"]
    # mozilla-taskcluster doesn't like scm_autoland, so special case it here
    # Once that is retired (Bug 1204891), this can be removed.
    if owner == "scm_autoland":
        owner = "scm_level_3"
    return owner


@pytest.mark.asyncio
@with_aiohttp_session
async def check_scopes():

    projects = await Project.fetch_all()
    tc_levels = {project.alias: project.access for project in projects}
    hgmo_levels = {
        project.alias: await get_repo_owner(project.repo) for project in projects
    }
    assert tc_levels == hgmo_levels
