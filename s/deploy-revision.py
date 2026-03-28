#!/usr/bin/env python3

import argparse
import re
import subprocess
import tempfile

# Workaround the limitation that az revision copy doesn't let you
# update multiple containers at once

parser = argparse.ArgumentParser()

parser.add_argument("--name", required=True)
parser.add_argument("--resource-group", required=True)
parser.add_argument("--git-hash", required=True)

args = parser.parse_args()

template_str = subprocess.check_output(
    f"az containerapp show --name {args.name} --resource-group {args.resource_group} --output yaml",
    shell=True,
).decode("utf-8")

regex = re.compile(r"rcpch.azurecr.io/npda-django:\w+")
template_str = regex.sub(f"rcpch.azurecr.io/npda-django:{args.git_hash}", template_str)

with tempfile.NamedTemporaryFile() as fp:
    fp.write(template_str.encode("utf-8"))

    subprocess.run(
        f"az containerapp update --name {args.name} --resource-group {args.resource_group} --yaml {fp.name} --query 'properties.provisioningState'",
        shell=True,
    )
