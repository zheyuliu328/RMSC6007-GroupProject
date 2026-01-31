#!/usr/bin/env bash
set -euo pipefail

RELEASE_DIR="release"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="methodd_snapshots_${TIMESTAMP}.zip"

mkdir -p "${RELEASE_DIR}"

if [ ! -d "MethodD/data/snapshots" ]; then
  echo "MethodD/data/snapshots 不存在，请先采集快照。"
  exit 1
fi

if [ -z "$(ls -A MethodD/data/snapshots 2>/dev/null)" ]; then
  echo "MethodD/data/snapshots 为空，无法打包。"
  exit 1
fi

zip -r "${RELEASE_DIR}/${ARCHIVE_NAME}" MethodD/data/snapshots \
  -x "MethodD/data/snapshots/runs/*"

echo "已生成：${RELEASE_DIR}/${ARCHIVE_NAME}"