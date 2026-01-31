#!/bin/bash
set -e
cd "$(dirname "$0")"
mkdir -p logs outputs
docker compose run --rm -T methodd
echo
echo "DONE. Outputs in ./outputs, logs in ./logs"
read -n 1 -s -r -p "Press any key to exit..."