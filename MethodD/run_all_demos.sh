#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
OUTPUT_DIR="${ROOT_DIR}/outputs"

mkdir -p "${LOG_DIR}" "${OUTPUT_DIR}" "${ROOT_DIR}/data"

RUN_TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_DIR}/run_${RUN_TS}.log"

{
  echo "========================================"
  echo "MethodD Demo Run - ${RUN_TS}"
  echo "========================================"
  echo "项目路径: ${ROOT_DIR}"
  echo "日志文件: ${LOG_FILE}"
  echo "输出目录: ${OUTPUT_DIR}"
  echo "========================================"
  echo

  echo "[1/3] 运行 IV 因子演示"
  python3 "${ROOT_DIR}/experiments/run_iv_factor_demo.py"
  echo

  echo "[2/3] 运行 NVDA 覆盖式卖 call 演示（离线真实快照复算）"
  python3 "${ROOT_DIR}/experiments/run_nvda_covered_call_demo.py"
  echo

  echo "[3/3] 运行 约束条件分析演示"
  python3 "${ROOT_DIR}/experiments/run_constraints_analysis.py"
  echo

  echo "========================================"
  echo "校验输出文件与日志"
  echo "========================================"

  echo "日志行数:"
  wc -l "${LOG_FILE}"
  echo

  echo "CSV 行数:"
  for csv_file in "${OUTPUT_DIR}"/*.csv; do
    if [[ -f "${csv_file}" ]]; then
      wc -l "${csv_file}"
    fi
  done
  echo

  echo "文件大小:"
  du -h "${LOG_FILE}" "${OUTPUT_DIR}"/* 2>/dev/null || true
  echo

  echo "生成哈希校验 (outputs/checksums.md5)"
  md5sum "${LOG_FILE}" "${OUTPUT_DIR}"/* > "${OUTPUT_DIR}/checksums.md5"

  echo "========================================"
  echo "运行结束"
  echo "========================================"
} 2>&1 | tee "${LOG_FILE}"