# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import click
import functools
import contextlib


class ClickOptionsRegistry:
    """A ClickOptionRegistry collects click options that can later be applied
    to a subcommand."""

    def __init__(self, name):
        self.options = []
        self.name = name

    def add(self, option):
        """Add an option to this registry.  For example,
        `generate_options.add(click.option(...))`.  Note that values for click
        options can later be recovered with
        `tcadmin.options.with_options`."""
        self.options.append(option)

    def apply(self, fn):
        """Apply the registered options to the given function.  This can be
        used as a decorator just like `click.option`."""
        for option in reversed(self.options):
            fn = option(fn)
        return fn


generate_options = ClickOptionsRegistry("generate_options")
output_options = ClickOptionsRegistry("output_options")
diff_options = ClickOptionsRegistry("diff_options")
check_options = ClickOptionsRegistry("check_options")
apply_options = ClickOptionsRegistry("apply_options")


@contextlib.contextmanager
def test_options(**options):
    "Context manager to set fake options"
    cmd = click.Command("test")
    ctx = click.Context(cmd)
    ctx.params.update(options)
    with ctx:
        yield


def with_options(*options):
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
