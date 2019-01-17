# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from ciadmin.generate import grants
from ciadmin.resources import Resources
from ciadmin.generate.ciconfig.projects import Project
from ciadmin.generate.ciconfig.grants import (
    Grant,
    ProjectGrantee,
    GroupGrantee,
)


@pytest.fixture
def add_scope():
    def add_scope(roleId, scope):
        add_scope.added.append((roleId, scope))
    add_scope.added = []
    return add_scope


class TestAddScopesForProjects:
    'Tests for add_scopes_to_projects'

    projects = [
        Project(
            alias='proj1',
            repo='https://hg.mozilla.org/foo/proj1',
            repo_type='hg',
            access='scm_level_1',
            trust_domain='gecko',
            features={
                'buildbot': False,
                'travis-ci': True,
            },
        ),
        Project(
            alias='proj2',
            repo='https://hg.mozilla.org/foo/proj2',
            repo_type='hg',
            access='scm_nss',
            trust_domain='nss',
            is_try=True,
        ),
    ]

    def test_no_match(self, add_scope):
        'If no projects match, it does not add scopes'
        grantee = ProjectGrantee(level=3)
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == []

    def test_no_scopes(self, add_scope):
        'If a projects matches, but no scopes are granted, nothing happens'
        grantee = ProjectGrantee(level=1)
        grants.add_scopes_for_projects(
            Grant(scopes=[], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == []

    def test_match_access(self, add_scope):
        'If access matches, it adds scopes'
        grantee = ProjectGrantee(access='scm_nss')
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj2:*', 'sc'),
        ]

    def test_match_level(self, add_scope):
        'If levels match, it adds scopes'
        grantee = ProjectGrantee(level=1)
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj1:*', 'sc'),
        ]

    def test_match_levels(self, add_scope):
        'If levels match (with multiple options) it adds scopes'
        grantee = ProjectGrantee(level=[1, 2])
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj1:*', 'sc'),
        ]

    def test_match_alias(self, add_scope):
        'If alias matches it adds scopes'
        grantee = ProjectGrantee(alias='proj1')
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj1:*', 'sc'),
        ]

    def test_match_feature(self, add_scope):
        'If feature matches it adds scopes'
        grantee = ProjectGrantee(feature='travis-ci')
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj1:*', 'sc'),
        ]

    def test_match_not_feature(self, add_scope):
        'If !feature matches it adds scopes'
        grantee = ProjectGrantee(feature='!travis-ci')
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj2:*', 'sc'),
        ]

    def test_match_is_try_false(self, add_scope):
        'If is_try matches and is false it adds scopes'
        grantee = ProjectGrantee(is_try=False)
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj1:*', 'sc'),
        ]

    def test_match_is_try_true(self, add_scope):
        'If is_try matches and is true it adds scopes'
        grantee = ProjectGrantee(is_try=True)
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj2:*', 'sc'),
        ]

    def test_match_trust_domain(self, add_scope):
        'If trust_domain matches it adds scopes'
        grantee = ProjectGrantee(trust_domain='gecko')
        grants.add_scopes_for_projects(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj1:*', 'sc'),
        ]

    def test_scope_substitution(self, add_scope):
        'Values alias, trust_domain, and level are substituted'
        grantee = ProjectGrantee(level=1)
        grants.add_scopes_for_projects(
            Grant(scopes=[
                'foo:{trust_domain}:level:{level}:{alias}'
            ], grantees=[grantee]),
            grantee, add_scope, self.projects)
        assert add_scope.added == [
            ('repo:hg.mozilla.org/foo/proj1:*', 'foo:gecko:level:1:proj1'),
        ]

    def test_scope_substitution_invalid_key(self, add_scope):
        'Substituting an unknown thing into a scope fails'
        grantee = ProjectGrantee(level=1)
        with pytest.raises(KeyError):
            grants.add_scopes_for_projects(
                Grant(scopes=['foo:{bar}'], grantees=[grantee]),
                grantee, add_scope, self.projects)

    def test_scope_substitution_no_level(self, add_scope):
        'A project without a level does not substitute {level} (fails)'
        grantee = ProjectGrantee(access='scm_nss')
        with pytest.raises(KeyError):
            grants.add_scopes_for_projects(
                Grant(scopes=['foo:{level}'], grantees=[grantee]),
                grantee, add_scope, self.projects)


class TestAddScopesForGroups:
    'Tests for add_scopes_to_groups'

    def test_no_groups(self, add_scope):
        'If no groups are given, nothing happens'
        grantee = GroupGrantee(groups=[])
        grants.add_scopes_for_groups(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope)
        assert add_scope.added == []

    def test_scopes_added(self, add_scope):
        'scopes are granted to groups, yay'
        grantee = GroupGrantee(groups=['group1', 'group2'])
        grants.add_scopes_for_groups(
            Grant(scopes=['sc'], grantees=[grantee]),
            grantee, add_scope)
        assert add_scope.added == [
            ('project:releng:ci-group:group1', 'sc'),
            ('project:releng:ci-group:group2', 'sc'),
        ]

    def test_substitution_fails(self, add_scope):
        '{..} in scopes is an error for groups'
        grantee = GroupGrantee(groups=['group1', 'group2'])
        with pytest.raises(KeyError):
            grants.add_scopes_for_groups(
                Grant(scopes=['level:{level}'], grantees=[grantee]),
                grantee, add_scope)


@pytest.mark.asyncio
async def test_update_resources(mock_ciconfig_file):
    mock_ciconfig_file('projects.yml', {
        'proj1': dict(
            repo='https://hg.mozilla.org/foo/proj1',
            repo_type='hg',
            access='scm_level_1',
            trust_domain='gecko',
        ),
    })
    mock_ciconfig_file('grants.yml', [{
        'grant': [
            'scope1:xyz',
            'scope1:abc',
            'scope2:*',
        ],
        'to': [{'project': {}}],
    }, {
        'grant': [
            'scope1:*',
            'scope2:abc',
        ],
        'to': [{'project': {}}],
    }])

    resources = Resources()
    resources.manage('Role=*')
    await grants.update_resources(resources, "dev")
    for resource in resources:
        if resource.id == 'Role=repo:hg.mozilla.org/foo/proj1:*':
            assert sorted(resource.scopes) == ['scope1:*', 'scope2:*']
            break
    else:
        assert 0, 'no role defined'
