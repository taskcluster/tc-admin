# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import pytest
from click.testing import CliRunner

import tcadmin.current
import tcadmin.util.root_url
from tcadmin.appconfig import AppConfig
from tcadmin.main import cli
from tcadmin.resources import Resources, Role


def role():
    # a function, as a Role can only be created with a current AppConfig
    return Role(roleId="test-role", description="", scopes=["scope"])


@pytest.fixture
def appconfig():
    appconfig = AppConfig()
    appconfig.root_url = "https://tc-testing.example.com"

    @appconfig.generators.register
    async def generate(resources):
        resources.manage("Role=test-role")
        resources.add(role())

    return appconfig


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in (
        "TASKCLUSTER_ROOT_URL",
        "TASKCLUSTER_CLIENT_ID",
        "TASKCLUSTER_ACCESS_TOKEN",
        "TASKCLUSTER_PROXY_URL",
    ):
        monkeypatch.delenv(var, raising=False)
    tcadmin.util.root_url._root_url = None
    yield
    tcadmin.util.root_url._root_url = None


def fake_current(monkeypatch, with_role):
    async def resources(managed):
        return Resources([role()] if with_role else [], managed)

    monkeypatch.setattr(tcadmin.current, "resources", resources)


def run(appconfig, *args):
    return CliRunner().invoke(cli(appconfig), list(args))


def test_diff_without_changes_exits_0(appconfig, monkeypatch):
    fake_current(monkeypatch, with_role=True)
    assert run(appconfig, "diff").exit_code == 0


def test_diff_with_changes_exits_2(appconfig, monkeypatch):
    fake_current(monkeypatch, with_role=False)
    assert run(appconfig, "diff").exit_code == 2


def test_diff_root_url_mismatch_exits_1(appconfig, monkeypatch):
    monkeypatch.setenv("TASKCLUSTER_ROOT_URL", "https://other.example.com")
    result = run(appconfig, "diff")
    assert result.exit_code == 1
    assert "TASKCLUSTER_ROOT_URL does not match" in result.output
    assert "Usage:" not in result.output


def test_diff_unknown_option_exits_1(appconfig):
    assert run(appconfig, "diff", "--no-such-option").exit_code == 1


def test_unknown_command_exits_1(appconfig):
    assert run(appconfig, "no-such-command").exit_code == 1


def test_apply_without_credentials_exits_1(appconfig):
    result = run(appconfig, "apply")
    assert result.exit_code == 1
    assert "TASKCLUSTER_CLIENT_ID must be set" in result.output
