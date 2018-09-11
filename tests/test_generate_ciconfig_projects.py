# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr
import pytest

from ciadmin.generate.ciconfig.projects import Project


@pytest.mark.asyncio
async def test_fetch_empty(mock_ciconfig_file):
    mock_ciconfig_file('projects.yml', {})
    assert await Project.fetch_all() == []


@pytest.mark.asyncio
async def test_fetch_defaults(mock_ciconfig_file):
    'Test a fetch of project data only the required fields, applying defaults'
    mock_ciconfig_file('projects.yml', {
        "ash": {
            "repo": "https://hg.mozilla.org/projects/ash",
            "repo_type": "hg",
            "access": "scm_level_2",
            "trust_domain": "gecko",
        }
    })
    prjs = await Project.fetch_all()
    assert len(prjs) == 1
    assert attr.asdict(prjs[0]) == {
        # alias
        "alias": "ash",
        # from file
        "repo": "https://hg.mozilla.org/projects/ash",
        "repo_type": "hg",
        "access": "scm_level_2",
        "trust_domain": "gecko",
        # defaults
        "is_try": False,
        "parent_repo": None,
        "features": {},
    }


@pytest.mark.asyncio
async def test_fetch_nodefaults(mock_ciconfig_file):
    'Test a fetch of project data with all required fields supplied'
    mock_ciconfig_file('projects.yml', {
        "ash": {
            "repo": "https://hg.mozilla.org/projects/ash",
            "repo_type": "hg",
            "access": "scm_level_2",
            "trust_domain": "gecko",
            "parent_repo": "https://hg.mozilla.org/mozilla-unified",
            "is_try": True,
            "features": {
                "taskcluster-push": True,
                "taskcluster-cron": False,
            },
        }
    })
    prjs = await Project.fetch_all()
    assert len(prjs) == 1
    assert attr.asdict(prjs[0]) == {
        # alias
        "alias": "ash",
        # from file
        "repo": "https://hg.mozilla.org/projects/ash",
        "repo_type": "hg",
        "access": "scm_level_2",
        "trust_domain": "gecko",
        "is_try": True,
        "parent_repo": "https://hg.mozilla.org/mozilla-unified",
        "features": {"taskcluster-push": True, "taskcluster-cron": False},
    }


def test_project_feature():
    'Test the feature method'
    prj = Project(alias='prj', repo='https://', repo_type='hg', access='scm_level_3', trust_domain='gecko',
                  features={'taskcluster-pull': True, 'taskcluster-cron': False})
    assert prj.feature('taskcluster-pull')
    assert not prj.feature('taskcluster-cron')
    assert not prj.feature('taskcluster-cron')
    assert not prj.feature('buildbot')


def test_project_enabled_features():
    'Test enabled_features'
    prj = Project(alias='prj', repo='https://', repo_type='hg', access='scm_level_3', trust_domain='gecko',
                  features={'taskcluster-pull': True, 'taskcluster-cron': False})
    assert prj.enabled_features == ['taskcluster-pull']


def test_project_level_property():
    'Test the level attribute'
    prj = Project(alias='prj', repo='https://', repo_type='hg', access='scm_level_3', trust_domain='gecko')
    assert prj.level == 3


def test_project_level_property_autoland():
    'Test the level property for scm_autoland'
    prj = Project(alias='prj', repo='https://', repo_type='hg', access='scm_autoland', trust_domain='gecko')
    assert prj.level == 3


def test_project_hmgo_path_property():
    'Test the hgmo_path property'
    prj = Project(alias='prj', repo='https://hg.mozilla.org/a/b/c', repo_type='hg',
                           access='scm_level_3', trust_domain='gecko')
    assert prj.hgmo_path == 'a/b/c'


def test_project_hmgo_path_property_trailing_slash():
    'Test the hgmo_path property stripping trialing slashes'
    prj = Project(alias='prj', repo='https://hg.mozilla.org/a/b/c/', repo_type='hg',
                           access='scm_level_3', trust_domain='gecko')
    assert prj.hgmo_path == 'a/b/c'


def test_project_hmgo_path_property_not_hg():
    'Test the hgmo_path property for non-hg projects'
    prj = Project(alias='prj', repo='https://github.com/a/b/c/', repo_type='git',
                           access='scm_level_3', trust_domain='gecko')
    with pytest.raises(AttributeError):
        prj.hgmo_path
