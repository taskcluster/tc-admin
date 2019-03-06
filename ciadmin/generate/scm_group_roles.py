# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

from ..resources import Role
from .ciconfig.projects import Project


async def update_resources(resources, environment):
    """
    Manage the `mozilla-group:active_scm_level_L` roles.

    These groups are assigned to everyone who has signed the appropriate paperwork to be a committer
    at level L.  In the current arrangement, they are granted all scopes available to all repos at
    level L or lower.  That is a lot, and there is work afoot to change it in bug 1470625.
    """
    resources.manage("Role=mozilla-group:active_scm_level_*")

    projects = await Project.fetch_all()

    for level in [1, 2, 3]:
        group = "active_scm_level_{}".format(level)
        roleId = "mozilla-group:" + group
        description = "Scopes automatically available to users at SCM level {}".format(
            level
        )
        scopes = ["assume:project:releng:ci-group:{}".format(group)]

        # include an `assume:` scope for each project at this level
        for project in projects:
            if project.access == "scm_level_{}".format(level):
                scopes.append(
                    "assume:repo:hg.mozilla.org/{}:*".format(project.repo_path)
                )

        if scopes:
            resources.add(Role(roleId=roleId, description=description, scopes=scopes))
