# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import json
import attr
import pytest
import textwrap

from ciadmin.resources.resources import Resource, Resources


@attr.s
class Thing(Resource):
    thingId = attr.ib(type=str)
    value = attr.ib(type=str)


@attr.s
class ListThing(Resource):
    listThingId = attr.ib(type=str)

    def things_formatter(value):
        return '\n'.join('- ' + e for e in value)
    things = attr.ib(type=list, metadata={'formatter': things_formatter})


def test_resource_attributes():
    'Resources have attributes'
    a = Thing('a', 'V')
    assert a.thingId == 'a'
    assert a.value == 'V'


def test_resource_comparison():
    'Resources should be ordered by their id'
    a = Thing('a', 'V')
    b = Thing('b', 'V')
    c = Thing('c', 'V')
    assert a < b
    assert a < c
    assert b < c


def test_resource_to_json():
    'Resources should have a `to_json` method that returns a dict'
    a = Thing('a', 'V')
    assert a.to_json() == dict(kind='Thing', thingId='a', value='V')


def test_resource_from_json():
    'Resource classes should have a `from_json` method that takes dict and creates an object'
    a = Resource.from_json({'kind': 'Thing', 'thingId': 'a', 'value': 'V'})
    assert a.thingId == 'a'
    assert a.value == 'V'


def test_resource_kind():
    'Resources should have an `kind` attribute naming the calss'
    a = Thing('a', 'V')
    assert a.kind == 'Thing'


def test_resource_id():
    'Resources should have an `id` attribute including the first attribute'
    a = Thing('a', 'V')
    assert a.id == 'Thing=a'


def test_resource_attr_immutable():
    'Any attribute is immutable'
    a = Thing('a', 'V')
    with pytest.raises(Exception):
        a.roleId = 'b'


def test_resource_id_immutable():
    'The `id` attribute is immutable'
    a = Thing('a', 'V')
    with pytest.raises(Exception):
        a.id = 'b'


def test_resource_str():
    'String formatting produces expected output'
    a = Thing('a', 'V')
    assert str(a) == textwrap.dedent('''\
      Thing=a:
        thingId: a
        value: V''')


def test_resource_multiline_str():
    'String formatting produces expected output with multiline values'
    a = Thing('a', 'V-line1\nV-line2')
    assert str(a) == textwrap.dedent('''\
      Thing=a:
        thingId: a
        value:
          V-line1
          V-line2''')


def test_resource_formatter():
    'String formatting produces expected output with a formatter'
    t = ListThing('lt', ['e1', 'e2', 'e3\nnewline'])
    assert str(t) == textwrap.dedent('''\
      ListThing=lt:
        listThingId: lt
        things:
          - e1
          - e2
          - e3
          newline''')


def test_resources_sorted():
    'Resources are always sorted'
    coll = Resources([
        Thing('z', '3'),
        Thing('x', '1'),
        Thing('y', '2'),
    ], ['Thing=*'])
    assert [r.thingId for r in coll] == ['x', 'y', 'z']


def test_resources_to_json():
    'Resources.to_json produces the expected data structure'
    rsrcs = Resources([
        Thing('x', '1'),
        Thing('y', '1'),
        ListThing('lt', ['1', '2']),
    ], ['Thing=*', 'ListThing=*'])
    assert rsrcs.to_json() == {
        'managed': [
            'ListThing=*',
            'Thing=*',
        ],
        'resources': [
            {'kind': 'ListThing', 'listThingId': 'lt', 'things': ['1', '2']},
            {'kind': 'Thing', 'thingId': 'x', 'value': '1'},
            {'kind': 'Thing', 'thingId': 'y', 'value': '1'}
        ],
    }


def test_resources_from_json():
    'Resources.from_json consumes a data structure and produces the expected result'
    json = {
        'managed': [
            'ListThing=*',
            'Thing=*',
        ],
        'resources': [
            {'kind': 'ListThing', 'listThingId': 'lt', 'things': ['1', '2']},
            {'kind': 'Thing', 'thingId': 'x', 'value': '1'},
            {'kind': 'Thing', 'thingId': 'y', 'value': '1'}
        ],
    }
    assert Resources.from_json(json) == Resources([
        Thing('x', '1'),
        ListThing('lt', ['1', '2']),
        Thing('y', '1'),
    ], ['ListThing=*', 'Thing=*'])


def test_resources_add_unmanaged_prohibited():
    'Adding an unmanaged resource is an error'
    with pytest.raises(RuntimeError, message='unmanaged resource: Thing=x'):
        rsrcs = Resources([], ['OtherStuff'])
        rsrcs.add(Thing('x', '1'))


def test_resources_manages():
    'Managing a resource adds it to the list of managed resources'
    rsrcs = Resources([], [])
    rsrcs.manage('Thing=x')
    assert list(rsrcs.managed) == ['Thing=x']


def test_resources_manages_minimal():
    'The list of managed resources is kept minimal (normalized)'
    rsrcs = Resources([], ['Thing=*', 'Other=x'])
    rsrcs.manage('Thing=x')
    assert list(rsrcs.managed) == ['Other=x', 'Thing=*']
    rsrcs.manage('Other=x')
    assert list(rsrcs.managed) == ['Other=x', 'Thing=*']
    rsrcs.manage('Othe*')
    assert list(rsrcs.managed) == ['Othe*', 'Thing=*']
    rsrcs.manage('*')
    assert list(rsrcs.managed) == ['*']


def test_resources_verify_duplicates_prohibited():
    'Duplicate resources are not allowed'
    with pytest.raises(RuntimeError, message='duplicate resources: Thing=x'):
        Resources([
            Thing('x', '1'),
            Thing('x', '1'),
        ], ['*'])


def test_resources_verify_unmanaged_prohibited():
    'Duplicate resources are not allowed'
    with pytest.raises(RuntimeError, message='unmanaged resources: ListThing=y'):
        Resources([
            Thing('x', '1'),
            ListThing('y', []),
        ], ['Thing=*'])


def test_resources_str():
    'Resources are stringified in order'
    resources = Resources([
        Thing('x', '1'),
        Thing('y', '1'),
    ], ['Thing=*', 'OtherStuff=*'])
    assert str(resources) == textwrap.dedent('''\
      managed:
        - OtherStuff=*
        - Thing=*

      resources:
        Thing=x:
          thingId: x
          value: 1

        Thing=y:
          thingId: y
          value: 1''')


def test_resources_repr():
    'Resources repr is pretty JSON'
    resources = Resources([
        Thing('x', '1'),
        Thing('y', '1'),
    ], ['*'])
    assert json.loads(repr(resources)) == json.loads('''\
	{
            "managed": [
                "*"
            ],
	    "resources": [
		{
		    "kind": "Thing",
		    "thingId": "x",
		    "value": "1"
		},
		{
		    "kind": "Thing",
		    "thingId": "y",
		    "value": "1"
		}
	    ]
	}''')

def test_resources_diff():
    'Diffing two resources returns a dif'
    left = Resources([Thing('a', 'no big deal'), Thing('x', 'abc')], ['*'])
    right = Resources([Thing('a', 'no big deal'), Thing('x', 'def')], ['*'])
    # note that this diff is selected to exercise the contextualize function, so "Thing=a:"
    # appears on the range line
    assert left.diff(right, fromfile='left', tofile='right') == textwrap.dedent('''\
        --- left
        +++ right
        @@ -8,4 +8,4 @@ Thing=a:

           Thing=x:
             thingId: x
        -    value: def
        +    value: abc''')
