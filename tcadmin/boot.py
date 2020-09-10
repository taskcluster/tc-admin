# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys

from .main import main


def bail(message):
    print(message, file=sys.stderr)
    sys.exit(1)


def find_tc_admin():
    # By default, look for tcadmin in the current directory
    tcadmin = "./tc-admin.py"

    # but also check a TC_ADMIN_PY env var
    try:
        tcadmin = os.environ["TC_ADMIN_PY"]
    except KeyError:
        pass

    # and look for a command-line option.  Click is not initialized yet
    # so we must scan the command line manually, and splice out the argument
    # if found
    for i, arg in enumerate(sys.argv):
        if arg == "--tc-admin-py":
            try:
                tcadmin = sys.argv[i + 1]
            except IndexError:
                bail("Error: --tc-admin-py requires an argument")
            sys.argv[i:i + 2] = []
        if arg.startswith("--tc-admin-py="):
            tcadmin = arg[len("--tc-admin-py="):]
            sys.argv[i:i + 1] = []

    return os.path.abspath(tcadmin)


def boot(main=main):
    tcadmin = find_tc_admin()
    if not os.path.exists(tcadmin):
        bail("Error: {} does not exist".format(tcadmin))

    # execute tc-admin.py to let it register all its callbacks, etc.
    with open(tcadmin) as f:
        code = compile(f.read(), tcadmin, "exec")

    dir = os.path.dirname(tcadmin)
    os.chdir(dir)

    globals = {"__file__": tcadmin}
    exec(code, globals, globals)
    try:
        appconfig = globals["appconfig"]
    except KeyError:
        bail("Error: tc-admin.py did not create a global variable `appconfig`")

    # finally, start the main command
    main(appconfig)


if __name__ == "__main__":
    boot()
