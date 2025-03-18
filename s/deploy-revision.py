#!/usr/bin/env python3

import argparse
import yaml
import tempfile
import subprocess

# Workaround the limitation that az revision copy doesn't let you
# update multiple containers at once

parser = argparse.ArgumentParser()

parser.add_argument("--name", required=True)
parser.add_argument("--resource-group", required=True)
parser.add_argument("--git-hash", required=True)

args = parser.parse_args()

template_str = subprocess.check_output(
    f"az containerapp show --name {args.name} --resource-group {args.resource_group} --output yaml",
    shell=True
).decode("utf-8")

template_yaml = yaml.safe_load(template_str)

for container in template_yaml["properties"]["template"]["containers"]:
    [image_name, _] = container["image"].split(":")
    container["image"] = f"{image_name}:{args.git_hash}"

with tempfile.NamedTemporaryFile() as fp:
    fp.write(yaml.dump(template_yaml).encode("utf-8"))

    subprocess.run(
        f"az containerapp update --name {args.name} --resource-group {args.resource_group} --yaml {fp.name} --query 'properties.provisioningState'",
        shell=True
    )