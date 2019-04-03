# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr

from .get import get_ciconfig_file

SYMBOLIC_GROUP_LEVELS = {"scm_versioncontrol": 3, "scm_autoland": 3, "scm_nss": 3}


@attr.s(frozen=True)
class Project:
    alias = attr.ib(type=str)
    repo = attr.ib(type=str)
    repo_type = attr.ib(type=str)
    access = attr.ib(
        type=str,
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    _level = attr.ib(
        type=int,
        default=None,
        validator=[
            attr.validators.optional(attr.validators.instance_of(int)),
            attr.validators.optional(attr.validators.in_([1, 2, 3])),
        ],
    )
    trust_domain = attr.ib(type=str, default=None)
    parent_repo = attr.ib(type=str, default=None)
    is_try = attr.ib(type=bool, default=False)
    features = attr.ib(type=dict, factory=lambda: {})

    def __attrs_post_init__(self):
        """Once the object is initialised, perform more sanity checks to ensure
        the values received are sane together"""
        # if neither `access` nor `level` are present, bail out
        if not self.access and not self._level:
            raise RuntimeError(
                "No access or level specified for project {}".format(self.alias)
            )
        # `access` is mandatory while `level` forbidden for hg based projects
        # and vice-versa for non-hg repositories
        if self.repo_type == "hg":
            if not self.access:
                raise ValueError(
                    "Mercurial repo {} needs to provide an input for "
                    "its `access` value".format(self.alias)
                )
            if self._level:
                raise ValueError(
                    "Mercurial repo {} cannot define a `level` "
                    "property".format(self.alias)
                )
        else:
            if not self._level:
                raise ValueError(
                    "Non-hg repo {} needs to provide an input for "
                    "its `level` value".format(self.alias)
                )
            if self.access:
                raise ValueError(
                    "Non-hg repo {} cannot define an `access` "
                    "property".format(self.alias)
                )

    @staticmethod
    async def fetch_all():
        """Load project metadata from projects.yml in ci-configuration"""
        projects = await get_ciconfig_file("projects.yml")
        return [Project(alias, **info) for alias, info in projects.items()]

    # The `features` property is designed for ease of use in yaml, with true and false
    # values for each feature; the `feature()` and `enabled_features` attributes provide
    # easier access for Python uses.

    def feature(self, feature):
        "Return True if this feature is enabled"
        return feature in self.features and self.features[feature]

    @property
    def enabled_features(self):
        "The list of enabled features"
        return [f for f, enabled in self.features.items() if enabled]

    def get_level(self):
        "Get the level, or None if the access level does not define a level"
        if self.access and self.access.startswith("scm_level_"):
            return int(self.access[-1])
        elif self.access and self.access in SYMBOLIC_GROUP_LEVELS:
            return SYMBOLIC_GROUP_LEVELS[self.access]
        elif self._level:
            return self._level
        else:
            return None

    @property
    def level(self):
        level = self.get_level()
        if level is None:
            raise RuntimeError(
                "unknown access {} for project {}".format(self.access, self.alias)
            )
        return level

    @property
    def repo_path(self):
        if self.repo_type == "hg" and self.repo.startswith("https://hg.mozilla.org/"):
            return self.repo.replace("https://hg.mozilla.org/", "").rstrip("/")
        elif self.repo_type == "git" and self.repo.startswith("https://github.com/"):
            return self.repo.replace("https://github.com/", "").rstrip("/")
        else:
            raise AttributeError(
                "no repo_path available for project {}".format(self.alias)
            )
