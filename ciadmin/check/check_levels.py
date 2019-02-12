# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest

from ciadmin.generate.ciconfig.projects import Project
from ciadmin.util.sessions import with_aiohttp_session, aiohttp_session


async def get_repo_scmlevel(repo):
    session = aiohttp_session()
    async with session.get("{}/json-repoinfo".format(repo)) as response:
        response.raise_for_status()
        result = await response.read()
    return json.loads(result)["group_owner"]


@pytest.mark.asyncio
@with_aiohttp_session
async def check_scopes():

    projects = await Project.fetch_all()
    tc_levels = {project.alias: project.access for project in projects}
    hgmo_levels = {
        project.alias: await get_repo_scmlevel(project.repo) for project in projects
    }
    assert tc_levels == hgmo_levels
