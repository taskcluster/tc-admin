# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster.async import Auth

from ..resources import Role
from ..util.sessions import aiohttp_session


async def fetch_roles(resources):
    auth = Auth(session=aiohttp_session())
    for role in await auth.listRoles():
        role = Role.from_api(role)
        if resources.is_managed(role.id):
            resources.add(role)
