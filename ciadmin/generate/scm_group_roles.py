# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

from tcadmin.resources import Role
from .ciconfig.projects import Project


async def update_resources(resources):
    """
    Manage the `mozilla-group:active_scm_level_L` roles.

    These groups are assigned to everyone who has signed the appropriate paperwork to be a committer
    at level L.  In the current arrangement, they are granted all scopes available to all repos at
    level L or lower.  That is a lot, and there is work afoot to change it in bug 1470625.
    """
    resources.manage("Role=mozilla-group:active_scm_level_[123]")

    projects = await Project.fetch_all()

    for level in [1, 2, 3]:
        group = "active_scm_level_{}".format(level)
        roleId = "mozilla-group:" + group
        description = "Scopes automatically available to users at SCM level {}".format(
            level
        )
        scopes = ["assume:project:releng:ci-group:{}".format(group)]

        # include an `assume:` scope for each project at level 1
        for project in projects:
            if project.level == 1 and project.repo_type == "hg":
                scopes.append("assume:{}:*".format(project.role_prefix))

        if scopes:
            resources.add(Role(roleId=roleId, description=description, scopes=scopes))
