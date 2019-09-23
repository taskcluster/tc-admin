# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from ..util.json import pretty_json

# utilities for resource attr.ib's
DESCRIPTION_PREFIX = """\
*DO NOT EDIT* - This resource is configured automatically.

"""


def description_converter(value):
    """Prepend *DO NOT EDIT* and a short explainer to the given value"""
    if not value.startswith("*DO NOT EDIT*"):
        value = DESCRIPTION_PREFIX + value
    return value


def scopes_converter(value):
    """Ensure that scopes are always sorted and immutable (a tuple)"""
    return tuple(sorted(value))


def list_formatter(value):
    """Format as a list of bulleted strings"""
    return "\n".join("- " + scope for scope in value)


def json_formatter(value):
    """Format as a pretty-printed JSON string"""
    return pretty_json(value)
