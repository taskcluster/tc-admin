# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .get import get_ciconfig_file


@attr.s(frozen=True)
class Project:
    alias = attr.ib(type=str)
    repo = attr.ib(type=str)
    repo_type = attr.ib(type=str)
    access = attr.ib(type=str)
    trust_domain = attr.ib(type=str, default=None)
    parent_repo = attr.ib(type=str, default=None)
    is_try = attr.ib(type=bool, default=False)
    features = attr.ib(type=dict, factory=lambda: {})
    extra_tc_scopes = attr.ib(type=list, factory=lambda: [])

    @staticmethod
    async def fetch_all():
        """Load project metadata from projects.yml in ci-configuration"""
        projects = await get_ciconfig_file('projects.yml')
        return [Project(alias, **info) for alias, info in projects.items()]

    # The `features` property is designed for ease of use in yaml, with true and false
    # values for each feature; the `feature()` and `enabled_features` attributes provide
    # easier access for Python uses.

    def feature(self, feature):
        'Return True if this feature is enabled'
        return feature in self.features and self.features[feature]

    @property
    def enabled_features(self):
        'The list of enabled features'
        return [f for f, enabled in self.features.items() if enabled]

    @property
    def level(self):
        if self.access.startswith('scm_level_'):
            return int(self.access[-1])
        elif self.access == 'scm_autoland':
            return 3
        else:
            raise RuntimeError("unknown access {} for project {}"
                               .format(self.access, self.alias))

    @property
    def hgmo_path(self):
        if self.repo_type == 'hg' and self.repo.startswith('https://hg.mozilla.org/'):
            return self.repo.replace('https://hg.mozilla.org/', '').rstrip('/')
        else:
            raise RuntimeError("no hgmo_path available for project {}".format(self.alias))
