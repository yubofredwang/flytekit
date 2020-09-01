from __future__ import absolute_import

import argparse
import logging
import subprocess
from os import environ
logging.basicConfig(level=logging.DEBUG)
FLYTE_ARG_PREFIX = "--__FLYTE"
FLYTE_ENV_VAR_PREFIX = f"{FLYTE_ARG_PREFIX}_ENV_VAR_"
FLYTE_CMD_PREFIX = f"{FLYTE_ARG_PREFIX}_CMD_"
FLYTE_ARG_SUFFIX = "__"

# An example for a valid command:
# --__FLYTE_ENV_VAR_env1__ val1 --__FLYTE_ENV_VAR_env2__ val2
# --__FLYTE_CMD_0_service_venv__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_1_pyflyte-execute__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_2_--task-module__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_3_blah__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_4_--task-name__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_5_bloh__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_6_--output-prefix__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_7_s3://fake-bucket__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_8_--inputs__ __FLYTE_CMD_DUMMY_VALUE__
# --__FLYTE_CMD_9_s3://fake-bucket__ __FLYTE_CMD_DUMMY_VALUE__

parser = argparse.ArgumentParser(description="Running sagemaker task")
args, unknowns = parser.parse_known_args()

# Parse the command line and env vars
flyte_cmd = []
env_vars = {}
i = 0

while i < len(unknowns):
    unknown = unknowns[i]
    logging.info(f'Processing argument {unknown}')
    if unknown.startswith(FLYTE_CMD_PREFIX) and unknown.endswith(FLYTE_ARG_SUFFIX):
        processed = unknown[len(FLYTE_CMD_PREFIX):][: -len(FLYTE_ARG_SUFFIX)]
        # Parse the format `1_--task-module`
        parts = processed.split('_', maxsplit=1)
        flyte_cmd.append((parts[0], parts[1]))
        i += 1
    elif unknown.startswith(FLYTE_ENV_VAR_PREFIX) and unknown.endswith(FLYTE_ARG_SUFFIX):
        processed = unknown[len(FLYTE_ENV_VAR_PREFIX):][: -len(FLYTE_ARG_SUFFIX)]
        i += 1
        if unknowns[i].startswith(FLYTE_ARG_PREFIX) is False:
            env_vars[processed] = unknowns[i]
            i += 1
    else:
        # To prevent SageMaker from ignoring our __FLYTE_CMD_*__ hyperparameters, we need to set a dummy value
        # which serves as a placeholder for each of them. The dummy value placeholder `__FLYTE_CMD_DUMMY_VALUE__`
        # falls into this branch and will be ignored
        i += 1

# Order the cmd using the index (the first element in each tuple)
flyte_cmd.sort(key=lambda x: x[0])
flyte_cmd = [x[1] for x in flyte_cmd]

logging.info(f"Cmd:{flyte_cmd}")
logging.info(f"Env vars:{env_vars}")

for key, val in env_vars.items():
    environ[key] = val

# Launching a subprocess with the selected entrypoint script and the rest of the arguments
logging.info(f"Launching command: {flyte_cmd}")
subprocess.run(flyte_cmd)
