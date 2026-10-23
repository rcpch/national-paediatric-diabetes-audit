#!/usr/bin/env python3

import argparse
import re
import shutil
import subprocess
import tempfile

# Workaround the limitation that az revision copy doesn't let you
# update multiple containers at once

parser = argparse.ArgumentParser()

parser.add_argument("--name", required=True)
parser.add_argument("--resource-group", required=True)
parser.add_argument("--git-hash", required=True)

args = parser.parse_args()

az = shutil.which("az")
if az is None:
    raise RuntimeError("az CLI not found in PATH")

template_str = subprocess.check_output(
    [
        az,
        "containerapp",
        "show",
        "--name",
        args.name,
        "--resource-group",
        args.resource_group,
        "--output",
        "yaml",
    ],
    text=True,
)

regex = re.compile(r"rcpch.azurecr.io/npda-django:\w+")
matches = regex.findall(template_str)
if not matches:
    print(
        "Warning: No image references found matching 'rcpch.azurecr.io/npda-django:*'"
    )
else:
    print(f"Updating {len(matches)} image reference(s) to tag '{args.git_hash}'")

template_str = regex.sub(f"rcpch.azurecr.io/npda-django:{args.git_hash}", template_str)

with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as fp:
    fp.write(template_str)
    fp.flush()  # Ensure YAML is written to disk before az reads it

    subprocess.run(
        [
            az,
            "containerapp",
            "update",
            "--name",
            args.name,
            "--resource-group",
            args.resource_group,
            "--yaml",
            fp.name,
            "--query",
            "properties.provisioningState",
        ],
        check=True,
    )
