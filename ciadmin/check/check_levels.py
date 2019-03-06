# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest

from ciadmin.generate.ciconfig.projects import Project
from ciadmin.util.sessions import with_aiohttp_session, aiohttp_session


async def get_hg_repo_owner(project):
    """
    Fetches the repo owner, in the form of unix group, from the
    hg.mozilla.org metadata
    """

    assert (
        project.repo_type == "hg"
    ), "Only hg repos can be queried for group_owner metadata"

    session = aiohttp_session()
    async with session.get("{}/json-repoinfo".format(project.repo)) as response:
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
async def check_scopes_for_hg_repos():
    """
    Ensures that the access levels present in the ci-configuration's
    `projects.yml` match the ones from hg.mozilla.org metadata
    """

    projects = await Project.fetch_all()
    tc_levels = {
        project.alias: project.access for project in projects if project.access
    }
    hgmo_levels = {
        project.alias: await get_hg_repo_owner(project)
        for project in projects
        if project.repo_type == "hg"
    }
    assert tc_levels == hgmo_levels
