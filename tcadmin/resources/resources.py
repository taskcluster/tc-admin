# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
import attr
import blessings
import functools
import textwrap
from memoized import memoized
from sortedcontainers import SortedKeyList

from ..util.matchlist import MatchList
from ..util.json import pretty_json

t = blessings.Terminal()


@functools.total_ordering
@attr.s(slots=True, frozen=True)
class Resource(object):
    """
    Base class for a single runtime configuration resource
    """

    @classmethod
    @memoized
    def _kind_classes(cls):
        return dict((c.__name__, c) for c in cls.__subclasses__())

    @classmethod
    def from_json(cls, json):
        """
        Given a kind and the result of to_json, create a new object

        Note that this modifies the given value in-place
        """
        kind = json.pop("kind")
        return cls._kind_classes()[kind](**json)

    def to_json(self):
        "Return a JSON-able version of this object, including a `kind` property"
        d = attr.asdict(self)
        d["kind"] = self.kind
        return d

    def to_api(self):
        "Construct a payload for Taskcluster API methods"
        raise NotImplementedError

    def merge(self, other):
        """
        Construct a 'merged' resource, given another resource with the same kind and id.

        Generally, resources can be merged if all fields either match or can be combined
        in some way, such as taking the union of scopesets
        """
        raise RuntimeError("Cannot merge resources of kind {}".format(self.kind))

    @property
    def kind(self):
        "The kind of this instance"
        return self.__class__.__name__

    @property
    def id(self):
        "The id of this instance, including the kind name"
        return "{}={}".format(
            self.kind, getattr(self, attr.fields(self.__class__)[0].name)
        )

    def evolve(self, **args):
        "Create a new resource like this one, but with the named attributes replaced"
        return attr.evolve(self, **args)

    def __str__(self):
        rv = ["{t.underline}{id}{t.normal}:".format(t=t, id=self.id)]
        for a in attr.fields(self.__class__):
            label = "  {t.bold}{a.name}{t.normal}:".format(t=t, a=a)
            formatted = a.metadata.get("formatter", lambda id, v: str(v))(
                self.id, getattr(self, a.name)
            )
            if "\n" in formatted:
                rv.append(label)
                rv.append(textwrap.indent(formatted, "    "))
            else:
                rv.append("{} {}".format(label, formatted))
        return "\n".join(rv)


@attr.s(repr=False)
class Resources:
    """
    Container class for multiple resource instances.

    This class also tracks what resources are "managed", allowing deletion of
    resources that are no longer defined.
    """

    resources = attr.ib(
        type=SortedKeyList,
        converter=lambda resources: SortedKeyList(resources, key=lambda r: r.id),
        default=[],
    )
    managed = attr.ib(
        type=MatchList,
        converter=lambda managed: MatchList(managed),
        default=MatchList([]),
    )

    def __attrs_post_init__(self):
        self._by_id = {r.id: r for r in self.resources}
        if len(self._by_id) != len(self.resources):
            raise RuntimeError("duplicate resources passed to Resources constructor")
        self._verify()

    def add(self, resource, _skip_verify=False):
        "Add the given resource to the collection"
        if not self.is_managed(resource.id):
            raise RuntimeError("unmanaged resource: " + resource.id)

        # if the resource already exists, try to merge it and remove the
        # previous version from the list of resources (SortedKeyList does not
        # support in-place replacement of items)
        if resource.id in self._by_id:
            existing = self._by_id[resource.id]
            resource = self._by_id[resource.id].merge(resource)
            idx = self.resources.index(existing)
            del self.resources[idx]

        self._by_id[resource.id] = resource
        self.resources.add(resource)

        if not _skip_verify:
            self._verify()

    def update(self, resources):
        "Add the given resources to the collection"
        for resource in resources:
            if not self.is_managed(resource.id):
                raise RuntimeError("unmanaged resource: " + resource.id)
            self.add(resource, _skip_verify=True)
        self._verify()

    def manage(self, pattern):
        "Add the given pattern to the list of managed resources"
        self.managed.add(pattern)

    def filter(self, pattern):
        """Return a new Resources object with only resources matching the given regexp. The
        'manages' property does not change."""
        reg = re.compile(pattern)
        return Resources(
            resources=[r for r in self.resources if reg.search(r.id)],
            managed=self.managed,
        )

    def map(self, functor):
        """Call functor for each resource in this collection, returning a new Resources
        containing the result."""
        return Resources(
            resources=[functor(r) for r in self.resources], managed=self.managed
        )

    def _verify(self):
        "Verify that this set of resources is legal (all managed, no duplicates)"

        unmanaged = sorted([r.id for r in self if not self.is_managed(r.id)])
        if unmanaged:
            raise RuntimeError("unmanaged resources: " + ", ".join(unmanaged))

    def is_managed(self, id):
        "Return True if the given id is managed"
        return self.managed.matches(id)

    def __iter__(self):
        return self.resources.__iter__()

    def __str__(self):
        self._verify()
        return "managed:\n{}\n\nresources:\n{}".format(
            "\n".join("  - " + m for m in self.managed),
            textwrap.indent("\n\n".join(str(r) for r in self), "  "),
        )

    def __repr__(self):
        return pretty_json(self.to_json())

    def to_json(self):
        "Convert to a JSON-able data structure"
        self._verify()
        return {"resources": [r.to_json() for r in self], "managed": list(self.managed)}

    @classmethod
    def from_json(cls, json):
        return Resources(
            (Resource.from_json(r) for r in json["resources"]), json["managed"]
        )
