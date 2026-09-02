# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from ..util.json import pretty_json


class Description(str):
    """A description string that remembers whether the value it was built
    from (before the boilerplate prefix was added) had any real content.
    """

    def __new__(cls, value, has_content):
        self = str.__new__(cls, value)
        self.has_content = has_content
        return self


def description_converter(value):
    """Prepend *DO NOT EDIT* and a short explainer to the given value"""
    from ..appconfig import AppConfig

    has_content = (
        value.has_content if isinstance(value, Description) else bool(value)
    )
    description_prefix = AppConfig.current().description_prefix
    if not value.startswith(description_prefix):
        value = description_prefix + value
    return Description(value, has_content)


def scopes_converter(value):
    """Ensure that scopes are always sorted and immutable (a tuple)"""
    return tuple(sorted(value))


def list_formatter(id, value):
    """Format as a list of bulleted strings"""
    return "\n".join("- " + scope for scope in value)


def json_formatter(id, value):
    """Format as a pretty-printed JSON string"""
    return pretty_json(value)
