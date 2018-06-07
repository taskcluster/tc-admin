# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import textwrap

from ciadmin.resources.resources import Resource
from ciadmin.resources.hook import Hook


@pytest.fixture(scope='module')
def simple_hook():
    return Hook(
        hookGroupId='garbage',
        hookId='test-hook',
        name='test',
        description='This is my hook',
        owner='me@me.com',
        emailOnError=False,
        schedule=[],
        task={'$magic': 'Siri, please test my code'},
        triggerSchema={})


def test_hook_id(simple_hook):
    'A hook id contains both hookGroupId and hookId'
    assert simple_hook.id == 'Hook=garbage/test-hook'


def test_hook_formatter(simple_hook):
    'Hooks are properly formatted with a string'
    print(simple_hook)
    assert str(simple_hook) == textwrap.dedent('''\
        Hook=garbage/test-hook:
          hookGroupId: garbage
          hookId: test-hook
          name: test
          description:
            *DO NOT EDIT* - This resource is configured automatically by [ci-admin](https://hg.mozilla.org/build/ci-admin).

            This is my hook
          owner: me@me.com
          emailOnError: False
          schedule: 
          task:
            {
                "$magic": "Siri, please test my code"
            }
          triggerSchema: {}''')


def test_role_from_api():
    'HOoks are properly read from a Taskcluster API result'
    api_result = {
        'hookGroupId': 'garbage',
        'hookId': 'test',
        'metadata': {
            'name': 'my-test',
            'description': '*DO NOT EDIT* - This resource is configured automatically by [ci-admin]'
            '(https://hg.mozilla.org/build/ci-admin).\n\nThis is my role',
            'owner': 'dustin@mozilla.com',
            'emailOnError': False,
        },
        'schedule': ['0 0 9,21 * * 1-5', '0 0 12 * * 0,6'],
        'task': {'$magic': 'build-task'},
        'triggerSchema': {},
    }
    hook = Hook.from_api(api_result)
    assert hook.hookGroupId == 'garbage'
    assert hook.hookId == 'test'
    assert hook.name == 'my-test'
    assert hook.description == api_result['metadata']['description']
    assert hook.owner == 'dustin@mozilla.com'
    assert hook.emailOnError == False
    assert hook.schedule == ('0 0 9,21 * * 1-5', '0 0 12 * * 0,6')
    assert hook.task == {'$magic': 'build-task'}
    assert hook.triggerSchema == {}
