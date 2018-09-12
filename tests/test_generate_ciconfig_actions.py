# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr
import pytest

from ciadmin.generate.ciconfig.actions import Action


@pytest.mark.asyncio
async def test_fetch_empty(mock_ciconfig_file):
    mock_ciconfig_file('actions.yml', [])
    assert await Action.fetch_all() == []


@pytest.mark.asyncio
async def test_fetch_entry(mock_ciconfig_file):
    mock_ciconfig_file('actions.yml', [
        {
            'trust_domain': 'gecko',
            'level': 1,
            'action_perm': 'generic',
        }
    ])
    assert await Action.fetch_all() == [
        Action(
            trust_domain='gecko',
            level=1,
            action_perm='generic',
            input_schema={
                'anyOf': [
                    {'type': 'object', 'description': 'user input for the task'},
                    {'const': None, 'description': 'null when the action takes no input'},
                ]
            },
        )
    ]


@pytest.mark.asyncio
async def test_fetch_entry_with_input_schema(mock_ciconfig_file):
    mock_ciconfig_file('actions.yml', [
        {
            'trust_domain': 'gecko',
            'level': 1,
            'action_perm': 'generic',
            'input_schema': {
                'type': 'string',
            },
        }
    ])
    assert await Action.fetch_all() == [
        Action(
            trust_domain='gecko',
            level=1,
            action_perm='generic',
            input_schema={'type': 'string'},
        )
    ]
