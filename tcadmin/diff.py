# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

import re
import click
import patiencediff
import blessings
import attr

from .util.ansi import strip_ansi
from .resources import Resources
from .options import with_options, diff_options

t = blessings.Terminal()


diff_options.add(
    click.option(
        "--ignore-descriptions/--include-descriptions",
        help="include (default) or ignore resource descriptions in compoarisons",
    )
)
diff_options.add(
    click.option("--grep", help="regular expression limiting resources displayed")
)
diff_options.add(
    click.option(
        "--unified",
        "-U",
        "context",
        type=int,
        default=8,
        help="number of lines of context to show",
    )
)
diff_options.add(
    click.option(
        "--ids-only",
        is_flag=True,
        help="only show resource IDs added (+), removed (-), or changed (@)",
    )
)


def id_diff(generated, current):
    generated_resources = {r.id: r for r in generated}
    current_resources = {r.id: r for r in current}
    all_resources = sorted(set(generated_resources) | set(current_resources))
    rv = []
    for id in all_resources:
        if id in generated_resources:
            if id in current_resources:
                g = generated_resources[id]
                c = current_resources[id]
                if c == g:
                    continue  # no difference
                if c.kind == g.kind:
                    c = attr.asdict(c)
                    g = attr.asdict(g)
                    fields = sorted(k for k in c if c[k] != g[k])
                else:
                    fields = ["kind"]
                rv.append(t.yellow("! {} (changed: {})".format(id, ", ".join(fields))))
            else:
                rv.append(t.green("+ {}".format(id)))
        else:
            rv.append(t.red("- {}".format(id)))
    return "\n".join(rv)


def textual_diff(generated, current, context):
    """
    Compare changes from Resources instances geneated and current, returning a
    string.
    """
    left = str(current).split("\n")
    right = str(generated).split("\n")
    resources_start = left.index("resources:")
    context_re = re.compile(r"^@@ -([0-9]*),")
    label_re = re.compile(r"^  ([^ ].*)")  # lines with exactly two spaces indentation

    def contextualize(rangeInfo):
        "add context information to range (@@ .. @@) line"
        match = context_re.match(rangeInfo)
        if not match:
            return ""
        line = int(match.group(1))
        while line > resources_start:
            line -= 1
            match = label_re.match(left[line])
            if match:
                return match.group(1)
        return ""

    lines = patiencediff.unified_diff(
        left, right, lineterm="", fromfile="current", tofile="generated", n=context
    )
    colors = {
        "-": lambda s: t.red(strip_ansi(s)),
        "+": lambda s: t.green(strip_ansi(s)),
        "@": lambda s: t.yellow(strip_ansi(s)) + " " + contextualize(s),
        " ": lambda s: s,
    }
    # colorize the lines
    lines = (
        colors[l[0]](l).rstrip() for l in (line if line else " " for line in lines)
    )
    return "\n".join(lines)


@with_options("ignore_descriptions", "grep", "ids_only", "context")
def show_diff(generated, current, ignore_descriptions, grep, ids_only, context):
    # limit the resources considered if --grep
    if grep:
        generated = generated.filter(grep)
        current = current.filter(grep)

    # reset descriptions to '' if --ignore-descriptions
    if ignore_descriptions:
        generated = Resources(
            managed=generated.managed,
            resources=(r.evolve(description="") for r in generated.resources),
        )
        current = Resources(
            managed=current.managed,
            resources=(r.evolve(description="") for r in current.resources),
        )

    if ids_only:
        result = id_diff(generated, current)
    else:
        result = textual_diff(generated, current, context)
    print(result)
    return result.strip() != ""
