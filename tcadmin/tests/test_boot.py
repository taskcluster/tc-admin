# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import textwrap
import os
import sys
import pytest

from tcadmin import boot

TC_ADMIN_PY = textwrap.dedent(
    """
    from tcadmin.appconfig import AppConfig
    appconfig = AppConfig()
    appconfig.check_path = 'kilroy-was-here'
    """
)


@pytest.fixture
def main(mocker):
    return mocker.Mock()


def test_boot_local_dir(main, tmp_path):
    (tmp_path / "tc-admin.py").write_text(TC_ADMIN_PY)
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        boot.boot(main)
        assert main.call_args[0][0].check_path == "kilroy-was-here"
    finally:
        os.chdir(old_cwd)


def test_boot_command_line(main, tmp_path, mocker):
    tc_admin_py = tmp_path / "tc-admin.py"
    tc_admin_py.write_text(TC_ADMIN_PY)
    sys.argv.extend(["--tc-admin-py", str(tc_admin_py)])
    try:
        boot.boot(main)
        assert main.call_args[0][0].check_path == "kilroy-was-here"
    finally:
        sys.argv[-2:] = []


def test_boot_env_var(main, tmp_path, mocker):
    tc_admin_py = tmp_path / "tc-admin.py"
    tc_admin_py.write_text(TC_ADMIN_PY)
    os.environ["TC_ADMIN_PY"] = str(tc_admin_py)
    try:
        boot.boot(main)
        assert main.call_args[0][0].check_path == "kilroy-was-here"
    finally:
        del os.environ["TC_ADMIN_PY"]
