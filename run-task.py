# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

"""
Run a ci-admin-related task, including cloning the repository and installing
Python packages.  The intent is to have a single, low-churn entry point to
the repository that can be called from a number of places: in-tree, in hooks,
and from both ci-admin and ci-configurations' .taskcluster.yml.  The task should
have

  image: python:3.5
  payload:
    env:
      # revision of ci-admin to check out (default: latest)
      CI_ADMIN_REVISION: ..
      # (usually omitted) repository containing ci-admin
      CI_ADMIN_REPOSITORY: ..
      # revision of ci-configuration to check out (default: latest)
      CI_CONFIGURATION_REVISION: ..
      # if 'tests', run the ci-admin and ci-configuration unit tests, lint, etc.
      # if 'diff', run `ci-admin diff'.
      RUN: 'tests'
    command:
      - bash
      - -c
      - >-
        wget https://hg.mozilla.org/ci/ci-admin/raw-file/default/run-task.py &&
        python run-task.py
"""

import sys


if sys.version_info[0:2] < (3, 5):
    print('run-task.py requires Python 3.5+')
    sys.exit(1)


import os
import datetime
import subprocess
import io
import re


REPO_DIR = '/tmp/ci-admin'


def print_line(prefix, m):
    now = datetime.datetime.utcnow().isoformat().encode('utf-8')
    # slice microseconds to 3 decimals.
    now = now[:-3] if now[-7:-6] == b'.' else now
    sys.stdout.buffer.write(b'[%s %sZ] %s' % (prefix, now, m))
    sys.stdout.buffer.flush()


def vcs_checkout(source_repo, dest, revision=None):
    args = ['hg', 'clone']
    if revision:
        args.extend(['-r', revision])
    args.extend([source_repo, dest])

    res = run_and_prefix_output(b'vcs', args)
    if res:
        sys.exit(res)

    # Update the current revision hash and ensure that it is well formed.
    revision = subprocess.check_output(
        ['hg', 'log',
         '--rev', '.',
         '--template', '{node}'],
        cwd=dest,
        # Triggers text mode on Python 3.
        universal_newlines=True)

    assert re.match('^[a-f0-9]{40}$', revision)

    print_line(b'vcs', 'Got revision {}\n'.format(revision).encode('utf-8'))


def run_and_prefix_output(prefix, args, extra_env={b'PYTHONUNBUFFERED': b'1'}, cwd='/'):
    # copied from taskcluster/scripts/run-task in-tree
    """Runs a process and prefixes its output with the time.

    Returns the process exit code.
    """
    print_line(prefix, b'executing %r in %r\n' % (args, cwd))

    env = dict(os.environ)
    env.update(extra_env or {})

    # Note: TaskCluster's stdin is a TTY. This attribute is lost
    # when we pass sys.stdin to the invoked process. If we cared
    # to preserve stdin as a TTY, we could make this work. But until
    # someone needs it, don't bother.

    # We want stdout to be bytes on Python 3. That means we can't use
    # universal_newlines=True (because it implies text mode). But
    # p.stdout.readline() won't work for bytes text streams. So, on Python 3,
    # we manually install a latin1 stream wrapper. This allows us to readline()
    # and preserves bytes, without losing any data.

    p = subprocess.Popen(args,
                         # Disable buffering because we want to receive output
                         # as it is generated so timestamps in logs are
                         # accurate.
                         bufsize=0,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         stdin=sys.stdin.fileno(),
                         cwd=cwd,
                         env=env)

    stdout = io.TextIOWrapper(p.stdout, encoding='latin1')

    while True:
        data = stdout.readline().encode('latin1')

        if data == b'':
            break

        print_line(prefix, data)

    return p.wait()


def main():
    ci_admin_repository = os.environ.get(
        'CI_ADMIN_REPOSITORY', 'https://hg.mozilla.org/build/ci-admin/')
    ci_admin_revision = os.environ.get('CI_ADMIN_REVISION')
    vcs_checkout(ci_admin_repository, REPO_DIR, ci_admin_revision)

    res = run_and_prefix_output(
        b'pip',
        [b'pip', b'install', b'-r', b'requirements.txt'],
        cwd=REPO_DIR)
    if res:
        sys.exit(res)

    run = os.environ.get('RUN')
    if run == 'tests':
        res = run_and_prefix_output(
            b'test',
            [b'python', b'setup.py', b'test'],
            cwd=REPO_DIR)
        if res:
            sys.exit(res)
    elif run == 'diff':
        # note that we ignore descriptions when diffing in ci, since they do not affect the
        # meaning of the resources
        diff_args = [b'python', b'-m', b'ciadmin.main', b'diff', b'--ignore-descriptions']
        if 'CI_CONFIGURATION_REVISION' in os.environ:
            diff_args.extend([
                b'--ci-configuration-revision',
                os.environ['CI_CONFIGURATION_REVISION'],
            ])
        res = run_and_prefix_output(b'diff', diff_args, cwd=REPO_DIR)
        if res:
            sys.exit(res)
    else:
        print_line('error', 'invalid RUN'.encode('utf-8'))
        sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
