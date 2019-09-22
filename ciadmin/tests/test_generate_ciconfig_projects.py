# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr
import pytest

from ciadmin.generate.ciconfig.projects import Project


@pytest.mark.asyncio
async def test_fetch_empty(mock_ciconfig_file):
    mock_ciconfig_file("projects.yml", {})
    assert await Project.fetch_all() == []


@pytest.mark.parametrize(
    "project_name,project_data,expected_data",
    (
        (
            "ash",
            {
                "repo": "https://hg.mozilla.org/projects/ash",
                "repo_type": "hg",
                "access": "scm_level_2",
                "trust_domain": "gecko",
            },
            {
                "alias": "ash",
                "repo": "https://hg.mozilla.org/projects/ash",
                "repo_type": "hg",
                "access": "scm_level_2",
                "trust_domain": "gecko",
                # defaults
                "_level": None,
                "is_try": False,
                "parent_repo": None,
                "features": {},
                "cron_targets": [],
            },
        ),
        (
            "fenix",
            {
                "repo": "https://github.com/mozilla-mobile/fenix/",
                "repo_type": "git",
                "level": 3,
            },
            {
                "alias": "fenix",
                "repo": "https://github.com/mozilla-mobile/fenix/",
                "repo_type": "git",
                # defaults
                "_level": 3,
                "access": None,
                "is_try": False,
                "parent_repo": None,
                "trust_domain": None,
                "features": {},
                "cron_targets": [],
            },
        ),
    ),
)
@pytest.mark.asyncio
async def test_fetch_defaults(
    mock_ciconfig_file, project_name, project_data, expected_data
):
    "Test a fetch of project data only the required fields, applying defaults"
    mock_ciconfig_file("projects.yml", {project_name: project_data})
    prjs = await Project.fetch_all()
    assert len(prjs) == 1
    assert attr.asdict(prjs[0]) == expected_data


@pytest.mark.parametrize(
    "project_name,project_data,expected_data",
    (
        (
            "ash",
            {
                "repo": "https://hg.mozilla.org/projects/ash",
                "repo_type": "hg",
                "access": "scm_level_2",
                "trust_domain": "gecko",
                "parent_repo": "https://hg.mozilla.org/mozilla-unified",
                "is_try": True,
                "features": {"hg-push": True, "gecko-cron": False},
                "cron_targets": ["a", "b"],
            },
            {
                # alias
                "alias": "ash",
                # from file
                "repo": "https://hg.mozilla.org/projects/ash",
                "repo_type": "hg",
                "access": "scm_level_2",
                "trust_domain": "gecko",
                "_level": None,
                "is_try": True,
                "parent_repo": "https://hg.mozilla.org/mozilla-unified",
                "features": {"hg-push": True, "gecko-cron": False},
                "cron_targets": ["a", "b"],
            },
        ),
        (
            "beetmoverscript",  # git project but not mobile
            {
                "repo": "https://github.com/mozilla-releng/beetmoverscript/",
                "repo_type": "git",
                "level": 3,
                "trust_domain": "beet",
                "parent_repo": "https://github.com/mozilla-releng/",
                "is_try": False,
                "features": {"hg-push": True, "gecko-cron": False},
                "cron_targets": ["a", "b"],
            },
            {
                # alias
                "alias": "beetmoverscript",
                # from file
                "repo": "https://github.com/mozilla-releng/beetmoverscript/",
                "repo_type": "git",
                "access": None,
                "trust_domain": "beet",
                "_level": 3,
                "is_try": False,
                "parent_repo": "https://github.com/mozilla-releng/",
                "features": {"hg-push": True, "gecko-cron": False},
                "cron_targets": ["a", "b"],
            },
        ),
    ),
)
@pytest.mark.asyncio
async def test_fetch_nodefaults(
    mock_ciconfig_file, project_name, project_data, expected_data
):
    "Test a fetch of project data with all required fields supplied"
    mock_ciconfig_file("projects.yml", {project_name: project_data})
    prjs = await Project.fetch_all()
    assert len(prjs) == 1
    assert attr.asdict(prjs[0]) == expected_data


def test_project_feature():
    "Test the feature method"
    prj = Project(
        alias="prj",
        repo="https://",
        repo_type="hg",
        access="scm_level_3",
        trust_domain="gecko",
        features={"taskcluster-pull": True, "gecko-cron": False},
    )
    assert prj.feature("taskcluster-pull")
    assert not prj.feature("gecko-cron")
    assert not prj.feature("gecko-cron")
    assert not prj.feature("buildbot")


def test_project_enabled_features():
    "Test enabled_features"
    prj = Project(
        alias="prj",
        repo="https://",
        repo_type="hg",
        access="scm_level_3",
        trust_domain="gecko",
        features={"taskcluster-pull": True, "gecko-cron": False},
    )
    assert prj.enabled_features == ["taskcluster-pull"]


@pytest.mark.parametrize(
    "project_data,expected_level",
    (
        (
            {
                "alias": "prj",
                "repo": "https://",
                "repo_type": "hg",
                "access": "scm_level_3",
                "trust_domain": "gecko",
            },
            3,
        ),
        (
            {
                "alias": "prj",
                "repo": "https://",
                "repo_type": "hg",
                "access": "scm_level_2",
                "trust_domain": "gecko",
            },
            2,
        ),
        (
            {
                "alias": "prj",
                "repo": "https://",
                "repo_type": "hg",
                "access": "scm_level_1",
                "trust_domain": "gecko",
            },
            1,
        ),
        (
            {
                "alias": "prj",
                "repo": "https://",
                "repo_type": "hg",
                "access": "scm_autoland",
                "trust_domain": "gecko",
            },
            3,
        ),
        ({"alias": "prj", "repo": "https://", "repo_type": "git", "level": 3}, 3),
        ({"alias": "prj", "repo": "https://", "repo_type": "git", "level": 1}, 1),
        ({"alias": "prj", "repo": "https://", "repo_type": "git", "level": 1}, 1),
    ),
)
def test_project_level_property(project_data, expected_level):
    "Test the level attribute"
    prj = Project(**project_data)
    assert prj.level == expected_level


@pytest.mark.parametrize(
    "project_data,error_type",
    (
        (
            {"alias": "prj", "repo": "https://", "repo_type": "git", "access": 10},
            TypeError,
        ),
        (
            {"alias": "prj", "repo": "https://", "repo_type": "git", "level": "10"},
            TypeError,
        ),
        (
            {"alias": "prj", "repo": "https://", "repo_type": "git", "level": 4},
            ValueError,
        ),
    ),
)
def test_project_level_failing_validators(project_data, error_type):
    "Test the level attribute"
    with pytest.raises(error_type):
        Project(**project_data)


@pytest.mark.parametrize(
    "project_data,error_type",
    (
        ({"alias": "prj", "repo": "https://", "repo_type": "git"}, RuntimeError),
        (
            {"alias": "prj", "repo": "https://", "repo_type": "hg", "level": 3},
            ValueError,
        ),
        (
            {
                "alias": "prj",
                "repo": "https://",
                "repo_type": "hg",
                "access": "scm_level_3",
                "level": 3,
            },
            ValueError,
        ),
        (
            {
                "alias": "prj",
                "repo": "https://",
                "repo_type": "git",
                "access": "scm_level_3",
            },
            ValueError,
        ),
        (
            {
                "alias": "prj",
                "repo": "https://",
                "repo_type": "git",
                "access": "scm_level_3",
                "level": 3,
            },
            ValueError,
        ),
        (
            {
                "alias": "prj",
                "repo": "https://",
                "repo_type": "hg",
                "access": "scm_mobile???",
            },
            RuntimeError,
        ),
    ),
)
def test_project_level_failing_post_init_checks(project_data, error_type):
    "Test the level attribute"
    with pytest.raises(error_type):
        prj = Project(**project_data)
        prj.level


def test_project_repo_path_property():
    "Test the repo_path property"
    prj = Project(
        alias="prj",
        repo="https://hg.mozilla.org/a/b/c",
        repo_type="hg",
        access="scm_level_3",
        trust_domain="gecko",
    )
    assert prj.repo_path == "a/b/c"


def test_project_repo_path_property_trailing_slash():
    "Test the repo_path property stripping trialing slashes"
    prj = Project(
        alias="prj",
        repo="https://hg.mozilla.org/a/b/c/",
        repo_type="hg",
        access="scm_level_3",
        trust_domain="gecko",
    )
    assert prj.repo_path == "a/b/c"


def test_project_repo_path_property_not_hg():
    "Test the repo_path property for non-{hg,git} projects"
    prj = Project(
        alias="prj",
        repo="https://subversionhub.com/a/b/c/",
        repo_type="svn",
        level=3,
        trust_domain="gecko",
    )
    with pytest.raises(AttributeError):
        prj.repo_path
