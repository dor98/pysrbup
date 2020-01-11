#!/usr/bin/env bash

set -o errexit -o errtrace -o nounset -o pipefail

DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
cd "${DIR}/.." || exit 1

echo 'Building pysrbup'

poetry install -v
python -m grpc_tools.protoc -I=proto --python_out=pysrbup --grpc_python_out=pysrbup proto/backup_system.proto
# Fix import paths. See also:
# - https://github.com/protocolbuffers/protobuf/issues/1491
# - https://github.com/protocolbuffers/protobuf/issues/881
# - https://github.com/grpc/grpc/issues/9575
sed -i -r 's/import (.+_pb2.*)/from pysrbup import \1/g' ./pysrbup/*_pb2*.py

pip install --editable .

echo 'Build complete'
