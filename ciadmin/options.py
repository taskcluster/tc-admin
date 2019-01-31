# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import click
import functools


def decorate(fn, *decorators):
    "Apply the given decorators to `fn`"
    for decorator in reversed(decorators):
        fn = decorator(fn)
    return fn


def with_click_options(*options):
    "When invoked, add the named Click options as keyword arguments to this function"

    def dec(fn):
        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            ctx = click.get_current_context()
            for opt in options:
                kwargs[opt] = ctx.params[opt]
            return fn(*args, **kwargs)

        wrap.unwrapped = fn  # for testing
        return wrap

    return dec
