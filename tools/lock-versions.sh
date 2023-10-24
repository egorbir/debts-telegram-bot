#!/bin/bash -u

set -o errexit
set -o errtrace
set -o pipefail

_APP_PATH=${APP_PATH}

_EXTRA_NEEDED=${EXTRA_NEEDED:-"false"}

EXTRA_ARGS=""

if [ "${_EXTRA_NEEDED}" = "true" ];
then
    EXTRA_ARGS="--extra-index-url=https://nexus.bostongene.internal/repository/pypi-all/simple"
fi

echo ${EXTRA_ARGS}

pip-compile \
    ${EXTRA_ARGS} \
    --build-isolation \
    ${_APP_PATH}/requirements.in \
    -o ${_APP_PATH}/requirements.txt
