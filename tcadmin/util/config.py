# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os
from abc import ABC, abstractmethod
import yaml


class Loader(ABC):
    async def load(self, filename, parse=None):
        """Load the given file.  If parse is `"yaml"` then the content is parsed
        as YAML; otherwise it is returned as a bytestring."""
        raw = await self.load_raw(filename)
        if parse == "yaml":
            return yaml.load(raw, Loader=yaml.Loader)
        elif parse:
            raise ValueError("Unknown parse format {}".format(parse))
        return raw

    @abstractmethod
    async def load_raw(self, filename):
        pass


class StaticLoader(Loader):
    def __init__(self, data):
        self.data = data

    async def load_raw(self, filename):
        raw = self.data[filename]
        if not isinstance(raw, bytes):
            return yaml.dump(raw)
        return raw


class LocalLoader(Loader):
    def __init__(self, directory="."):
        self.directory = directory

    async def load_raw(self, filename):
        with open(os.path.join(self.directory, filename), "rb") as f:
            return f.read()


class ConfigList(list):
    @classmethod
    async def load(cls, loader):
        data = await loader.load(cls.filename, parse="yaml")
        assert isinstance(data, list), "{} is not a YAML array".format(cls.filename)
        return cls(cls.Item(**cls.transform_item(item)) for item in data)

    @classmethod
    def transform_item(cls, item):
        return item


class ConfigDict(dict):
    @classmethod
    async def load(cls, loader):
        data = await loader.load(cls.filename, parse="yaml")
        assert isinstance(data, dict), "{} is not a YAML object".format(cls.filename)
        return cls((k, cls.Item(k, **cls.transform_item(v))) for k, v in data.items())

    @classmethod
    def transform_item(cls, item):
        return item
