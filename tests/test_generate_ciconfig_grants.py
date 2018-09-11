# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr
import pytest

from ciadmin.generate.ciconfig.grants import (
    Grant,
    ProjectGrantee,
    GroupGrantee,
)


@pytest.mark.asyncio
async def test_fetch_empty(mock_ciconfig_file):
    mock_ciconfig_file('grants.yml', [])
    assert await Grant.fetch_all() == []


@pytest.mark.asyncio
async def test_fetch_entries(mock_ciconfig_file):
    '''Test fetching non-empty grants, including singular and plural names'''
    mock_ciconfig_file('grants.yml', [
        {
            'grant': ['somescope'],
            'to': [
                # an entry with only one condition (singular)
                {'project': {'level': 3}},
                # an entry with lots of conditions (plural)
                {'projects': {
                    'access': 'scm_level_3',
                    'level': 3,
                    'alias': ['myproject', 'yours'],
                    'feature': ['buildbot'],
                    'is_try': True,
                    'trust_domain': 'nss',
                    'job': 'cron:*',
                }},
            ],
        }, {
            'grant': ['userscope'],
            'to': [
                {'group': ['a', 'b']},
                {'groups': 'c'},
            ],
        }
    ])

    grants = await Grant.fetch_all()
    assert grants == [
        Grant(
            scopes=['somescope'],
            grantees=[
                ProjectGrantee(level=3),
                ProjectGrantee(
                    access='scm_level_3',
                    level=3,
                    alias=['myproject', 'yours'],
                    feature='buildbot',
                    is_try=True,
                    trust_domain='nss',
                    job='cron:*')
            ]),
        Grant(
            scopes=['userscope'],
            grantees=[
                GroupGrantee(groups=['a', 'b']),
                GroupGrantee(groups=['c']),
            ]),
    ]

    # check out the structure more deeply, to check None and listifying
    grantee = grants[0].grantees[0]
    assert grantee.level == [3]
    assert grantee.alias == None
    assert grantee.is_try == None
    assert grantee.job == ['*']

    grantee = grants[0].grantees[1]
    assert grantee.access == ['scm_level_3']
    assert grantee.level == [3]
    assert grantee.alias == ['myproject', 'yours']
    assert grantee.feature == ['buildbot']
    assert grantee.is_try == True
    assert grantee.trust_domain == ['nss']
    assert grantee.job == ['cron:*']

    grantee = grants[1].grantees[0]
    assert grantee.groups == ['a', 'b']

    grantee = grants[1].grantees[1]
    assert grantee.groups == ['c']


@pytest.mark.asyncio
async def test_fetch_grants_to_not_list(mock_ciconfig_file):
    'Fetching grants.yml a malformed grants.to is an error'
    mock_ciconfig_file('grants.yml', [
        {
            'grant': [1, 2, 3],
            'to': 'example-user:frankie'
        }
    ])

    with pytest.raises(ValueError):
        await Grant.fetch_all()


@pytest.mark.asyncio
async def test_fetch_non_string_scopes(mock_ciconfig_file):
    'Fetching grants.yml with non-strings scopes is an error'
    mock_ciconfig_file('grants.yml', [
        {
            'grant': [1, 2, 3],
            'to': [],
        }
    ])

    with pytest.raises(ValueError):
        await Grant.fetch_all()


@pytest.mark.asyncio
async def test_fetch_non_list_scopes(mock_ciconfig_file):
    'Fetching grants.yml with something other than a list of scopes is an error'
    mock_ciconfig_file('grants.yml', [
        {
            'grant': None,
            'to': [],
        }
    ])

    with pytest.raises(ValueError):
        await Grant.fetch_all()


@pytest.mark.asyncio
async def test_fetch_invalid_project_grantee_too_many_keys(mock_ciconfig_file):
    'A grantee with too many keys (not just project or group) is an error'
    mock_ciconfig_file('grants.yml', [
        {
            'grant': [],
            'to': [
                # this is easy to do in YAML..
                {'project': None, 'level': 3},
            ],
        }
    ])

    with pytest.raises(ValueError):
        await Grant.fetch_all()


@pytest.mark.asyncio
async def test_fetch_invalid_group_grantee(mock_ciconfig_file):
    'A malformed group grantee is an error'
    mock_ciconfig_file('grants.yml', [
        {
            'grant': [],
            'to': [
                {'groups': {'admins': True}},
            ],
        }
    ])

    with pytest.raises(ValueError):
        await Grant.fetch_all()


@pytest.mark.asyncio
async def test_fetch_invalid_grantee_too_many_keys(mock_ciconfig_file):
    'A grantee with an invalid key is an error'
    mock_ciconfig_file('grants.yml', [
        {
            'grant': [],
            'to': [
                {'user': 'me'},
            ],
        }
    ])

    with pytest.raises(ValueError):
        await Grant.fetch_all()
