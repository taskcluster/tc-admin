# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
from ..util import pretty_json

# utilities for resource attr.ib's
DESCRIPTION_PREFIX = '''\
*DO NOT EDIT* - This resource is configured automatically by [ci-admin](https://hg.mozilla.org/build/ci-admin).

'''


def description_converter(value):
    '''Prepend *DO NOT EDIT* and a short explainer to the given value'''
    if not value.startswith('*DO NOT EDIT*'):
        value = DESCRIPTION_PREFIX + value
    return value


def scopes_converter(value):
    '''Ensure that scopes are always sorted and immutable (a tuple)'''
    value.sort()
    return tuple(value)


def list_formatter(value):
    '''Format as a list of bulleted strings'''
    return '\n'.join('- ' + scope for scope in value)


def json_formatter(value):
    '''Format as a pretty-printed JSON string'''
    return pretty_json(value)


# from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
ANSI_ESCAPE = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')


def strip_ansi(line):
    'Strip ANSI color codes from a line of text (used to colorize diffs)'
    return ANSI_ESCAPE.sub('', line)
