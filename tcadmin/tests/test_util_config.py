# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os
import yaml
import attr

from tcadmin.util.config import ConfigList, ConfigDict, LocalLoader, StaticLoader


def test_local_loader():
    dir = os.path.dirname(__file__)
    loader = LocalLoader(dir)
    assert yaml.load(loader.load_raw("testfile.yml")) == {"data": [1, 2]}


def test_local_loader_parse():
    dir = os.path.dirname(__file__)
    loader = LocalLoader(dir)
    assert loader.load("testfile.yml", parse="yaml") == {"data": [1, 2]}


def test_local_loader_no_parse():
    dir = os.path.dirname(__file__)
    loader = LocalLoader(dir)
    assert yaml.load(loader.load("testfile.yml")) == {"data": [1, 2]}


def test_static_loader_yaml():
    loader = StaticLoader({"data.yml": {"foo": "bar"}})
    assert yaml.load(loader.load_raw("data.yml")) == {"foo": "bar"}


def test_static_loader_raw():
    loader = StaticLoader({"data.bin": b"abcd"})
    assert loader.load_raw("data.bin") == b"abcd"


loader = StaticLoader(
    {
        "kvs.yml": [{"k": "a", "v": 1}, {"k": "b", "v": 2}, 3],
        "nicknames.yml": {
            "Gertie": {"fullname": "Gertrude", "historical": True},
            "Josie": "Josephine",
        },
    }
)


class KVs(ConfigList):
    filename = "kvs.yml"

    @classmethod
    def transform_item(cls, item):
        if isinstance(item, int):
            return {"k": str(item), "v": item}
        return item

    @attr.s
    class Item:
        k = attr.ib(type=str)
        v = attr.ib(type=int)

    def sum_values(self):
        return sum(i.v for i in self)


def test_config_array():
    kvs = KVs.load(loader)
    assert kvs[0].k == "a"
    assert kvs[0].v == 1
    assert kvs[1].k == "b"
    assert kvs[1].v == 2
    assert kvs[2].k == "3"
    assert kvs[2].v == 3
    assert kvs.sum_values() == 6


class Nicknames(ConfigDict):
    filename = "nicknames.yml"

    @classmethod
    def transform_item(cls, item):
        if isinstance(item, str):
            return {"fullname": item}
        return item

    @attr.s
    class Item:
        nick = attr.ib(type=str)
        fullname = attr.ib(type=str)
        historical = attr.ib(type=bool, default=False)


def test_config_dict():
    nicks = Nicknames.load(loader)
    assert nicks["Gertie"].fullname == "Gertrude"
