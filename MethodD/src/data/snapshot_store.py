"""
快照存取模块：负责期权链快照与 manifest 管理
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Optional

import pandas as pd


SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'snapshots')
RUNS_DIR = os.path.join(SNAPSHOT_DIR, 'runs')


def _ensure_dir(path: Optional[str] = None) -> None:
    os.makedirs(path or SNAPSHOT_DIR, exist_ok=True)


def _ensure_runs_dir() -> None:
    os.makedirs(RUNS_DIR, exist_ok=True)


def resolve_run_dir(run_id: str) -> str:
    _ensure_runs_dir()
    return os.path.join(RUNS_DIR, run_id)


def _timestamp_tag() -> str:
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def write_snapshot(snapshot: Dict[str, object], label: str) -> str:
    """写入期权链快照文件，返回路径"""
    _ensure_dir()
    filename = f"nvda_chain_{label}_{_timestamp_tag()}.json"
    path = os.path.join(SNAPSHOT_DIR, filename)

    payload = {
        'ticker': snapshot.get('ticker'),
        'spot': snapshot.get('spot'),
        'timestamp': snapshot.get('timestamp'),
        'chain': snapshot.get('chain').to_dict(orient='records') if isinstance(snapshot.get('chain'), pd.DataFrame) else snapshot.get('chain')
    }

    with open(path, 'w', encoding='utf-8') as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    return path


def write_checksum(file_path: str) -> str:
    """写入单文件 checksum（sha256），返回 checksum 文件路径"""
    _ensure_dir()
    checksum_path = f"{file_path}.sha256"
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(8192), b''):
            sha256.update(chunk)
    digest = sha256.hexdigest()
    with open(checksum_path, 'w', encoding='utf-8') as file:
        file.write(f"{digest}  {os.path.basename(file_path)}\n")
    return checksum_path


def write_manifest(manifest: Dict[str, object], run_id: Optional[str] = None) -> str:
    """写入 manifest.json（支持 run_id 目录）"""
    if run_id:
        run_dir = resolve_run_dir(run_id)
        _ensure_dir(run_dir)
        path = os.path.join(run_dir, 'manifest.json')
    else:
        _ensure_dir()
        path = os.path.join(SNAPSHOT_DIR, 'manifest.json')
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    return path


def load_manifest(run_id: Optional[str] = None) -> Optional[Dict[str, object]]:
    """读取 manifest.json（支持 run_id 目录）"""
    if run_id:
        path = os.path.join(resolve_run_dir(run_id), 'manifest.json')
    else:
        path = os.path.join(SNAPSHOT_DIR, 'manifest.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


def load_checksum(file_path: str) -> str:
    """读取单文件 checksum（sha256）"""
    checksum_path = f"{file_path}.sha256"
    if not os.path.exists(checksum_path):
        raise FileNotFoundError(f"缺少 checksum 文件: {checksum_path}")
    with open(checksum_path, 'r', encoding='utf-8') as file:
        content = file.read().strip()
    if not content:
        raise ValueError(f"checksum 文件为空: {checksum_path}")
    return content.split()[0]


def verify_checksum(file_path: str) -> None:
    """校验单文件 checksum，不匹配直接抛错"""
    expected = load_checksum(file_path)
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(8192), b''):
            sha256.update(chunk)
    actual = sha256.hexdigest()
    if actual != expected:
        raise ValueError(f"checksum 不一致: {os.path.basename(file_path)} expected={expected} actual={actual}")


def resolve_snapshot_path(filename: str, run_id: Optional[str] = None) -> str:
    """从 snapshot 目录拼接路径（支持 run_id 目录）"""
    if run_id:
        return os.path.join(resolve_run_dir(run_id), filename)
    return os.path.join(SNAPSHOT_DIR, filename)


def list_run_manifests() -> Dict[str, str]:
    """列出 runs 目录下所有 manifest.json"""
    _ensure_runs_dir()
    manifests = {}
    for name in os.listdir(RUNS_DIR):
        run_dir = os.path.join(RUNS_DIR, name)
        manifest_path = os.path.join(run_dir, 'manifest.json')
        if os.path.isdir(run_dir) and os.path.exists(manifest_path):
            manifests[name] = manifest_path
    return manifests