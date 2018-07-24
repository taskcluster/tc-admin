# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .get import get_ciconfig_file


def listify(x):
    'Return a list, converting single items to singleton lists; but keep None'
    if x is None:
        return x
    if isinstance(x, list):
        return x
    return [x]


@attr.s(frozen=True)
class ProjectGrantee:
    access = attr.ib(type=list, converter=listify, default=None)
    level = attr.ib(type=list, converter=listify, default=None)
    alias = attr.ib(type=list, converter=listify, default=None)
    feature = attr.ib(type=list, converter=listify, default=None)
    is_try = attr.ib(type=bool, default=None)
    trust_domain = attr.ib(type=list, converter=listify, default=None)
    job = attr.ib(type=list, converter=listify, default='*')


@attr.s(frozen=True)
class GroupGrantee:
    groups = attr.ib(type=list, converter=listify, default=None)


@attr.s(frozen=True)
class Grant:
    scopes = attr.ib(type=list, factory=lambda: [])
    grantees = attr.ib(type=list, factory=lambda: [])

    @scopes.validator
    def validate_scopes(self, attribute, value):
        if not isinstance(value, list):
            raise ValueError('scopes must be a list')
        if any(not isinstance(s, str) for s in value):
            raise ValueError('scopes must be a list of strings')

    @staticmethod
    async def fetch_all():
        """Load project metadata from grants.yml in ci-configuration"""
        grants = await get_ciconfig_file('grants.yml')

        # convert grantees into instances..
        def grantee_instance(grantee):
            if len(grantee) != 1:
                raise ValueError('Malformed grantee (too many keys): %s'.format(grantee))
            kind, content = list(grantee.items())[0]

            if kind == 'project' or kind == 'projects':
                return ProjectGrantee(**content)
            elif kind == 'group' or kind == 'groups':
                return GroupGrantee(groups=content)
            else:
                raise ValueError('Malformed grantee (invalid top-level key): %s'.format(grantee))

        return [Grant(scopes=grant['grant'], grantees=[grantee_instance(ge) for ge in grant['to']]) for grant in grants]
