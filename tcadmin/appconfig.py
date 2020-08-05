# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import attr
import asyncio
from contextlib import contextmanager

from .callbacks import CallbacksRegistry


import click


class CallablesRegistry:
    """A registry collects (async) callables for a specific purpose.

    The `register` method of a CallablesRegistry can be used as a decorator.
    """

    def __init__(self, name):
        self.callables = []
        self.name = name

    def register(self, callable):
        self.callables.append(callable)
        return callable

    def __iter__(self):
        return self.callables.__iter__()

    async def _call_all(self, *args, **kwargs):
        """Call all of the callables at the same time, waiting until they all
        complete."""
        await asyncio.gather(*(c(*args, **kwargs) for c in self.callables))


class OptionsRegistry:
    """A registry that collects command-line options."""

    def __init__(self, name):
        self.option_args = {}
        # mapping of `--foo` to the name click selected for it
        self.option_names = {}
        self.name = name

        # special case for --with-secrets
        self.option_names["--with-secrets"] = "with_secrets"

    def add(self, name, *, required=False, help=None, default=None):
        """
        Register a command-line option.  Once options are parsed, the value
        will be available from the `get` method.
        """

        assert name.startswith("--"), "option must be of the form --foo"
        kwargs = {}
        if required:
            kwargs["required"] = required
        if help:
            kwargs["help"] = help
        if default:
            kwargs["default"] = default
        self.option_args[name] = kwargs

        # get click to generate a name for this
        opt = click.Option((name,), **kwargs)
        self.option_names[name] = opt.name

    def get(self, name):
        """Get a value for a command-line options"""
        ctx = click.get_current_context()
        try:
            click_name = self.option_names[name]
        except KeyError:
            try:
                # fall back to reading built-in tc-admin options
                click_name = name
                ctx.params[click_name]
            except KeyError:
                raise KeyError("No option named {} is registered".format(name))
        return ctx.params[click_name]

    def _apply(self, fn):
        for name, kwargs in self.option_args.items():
            fn = click.option(name, **kwargs)(fn)
        return fn


@attr.s(slots=True)
class AppConfig:
    """
    An object storing the configuration for tc-admin itself, including functions to
    generate resources.  This is typically created by tc-admin.py.
    """

    # The path to the directory containing the check implementations; this will be
    # treated as relative to the current directory.
    check_path = attr.ib(type=str, init=False, default="checks")

    # utilities for resource attr.ib's
    description_prefix = attr.ib(
        type=str,
        init=False,
        default="*DO NOT EDIT* - This resource is configured automatically.\n\n",
    )

    # Command-line options for the resource-generation process
    options = attr.ib(init=False, factory=lambda: OptionsRegistry("options"))

    # Resource generators, each called with a Resources object and expected to
    # update that object accordingly
    generators = attr.ib(init=False, factory=lambda: CallablesRegistry("generators"))

    # Resource modifiers, each called with a resources object and expected to return
    # a new set of resources (such as with `resources.map` or `resources.filter`)
    modifiers = attr.ib(init=False, factory=lambda: CallablesRegistry("modifiers"))

    # Callbacks to trigger a custom action during the apply workflow
    # * before_apply will gives access to resources before they are modified
    # * after_apply will gives access to resources after they are modified
    callbacks = attr.ib(init=False, factory=lambda: CallbacksRegistry())

    @classmethod
    def current(cls):
        """Get the current AppConfig"""
        assert getattr(cls, "_current", None), "no current AppConfig"
        return cls._current

    @classmethod
    @contextmanager
    def _as_current(cls, current):
        """Set the current AppConfig.  This is only used within tcadmin itself"""
        old = getattr(cls, "_current", None)
        try:
            cls._current = current
            yield
        finally:
            cls._current = old
