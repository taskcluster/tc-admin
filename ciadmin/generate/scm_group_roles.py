# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import absolute_import, print_function, unicode_literals

from ..resources import Role
from .projects import Project
from .actions import Action


async def update_resources(resources):
    '''
    Manage the `mozilla-group:active_scm_level_L` roles.

    These groups are assigned to everyone who has signed the appropriate paperwork to be a committer
    at level L.  In the current arrangement, they are granted all scopes available to all repos at
    level L or lower.  That is a lot, and there is work afoot to change it!
    '''
    resources.manage('Role=mozilla-group:active_scm_level_*')

    projects = await Project.fetch_all()
    actions = await Action.fetch_all()

    for level in [1, 2, 3]:
        group = 'active_scm_level_{}'.format(level)
        roleId = 'mozilla-group:' + group
        description = 'Scopes automatically available to users at SCM level {}'.format(level)
        scopes = []

        # include an `assume:` scope for each project at this level
        for project in projects:
            if project.access == 'scm_level_{}'.format(level):
                scopes.append('assume:repo:hg.mozilla.org/{}:*'.format(project.hgmo_path))

        # refer to the in-tree-action-trigger roles for permission to trigger any defined actions
        trust_domains = set(a.trust_domain for a in actions if a.level == level and group in a.groups)
        for trust_domain in trust_domains:
            scopes.append('assume:project:{}:in-tree-action-trigger:active_scm_level_{}'.format(trust_domain, level))

        if scopes:
            resources.add(Role(roleId=roleId, description=description, scopes=scopes))
