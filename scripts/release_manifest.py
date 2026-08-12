#!/usr/bin/env python3
"""Create a deterministic source-and-evidence manifest for AGI-VS releases."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path


MANIFEST_FILES = (
    "CMakeLists.txt",
    "alvs_core.h",
    "alvs_core.cpp",
    "bindings.cpp",
    "stage1_evaluation.cpp",
    "stage2_evaluation.cpp",
    "stage3_evaluation.cpp",
    "stage4_evaluation.cpp",
    "stage5_evaluation.cpp",
    "stage4_python_evaluation.py",
    "stage5_python_evaluation.py",
    "Stages/stage1_native_full_results.txt",
    "Stages/stage2_native_full_results.txt",
    "Stages/stage3_native_full_results.txt",
    "Stages/stage4_native_full_results.txt",
    "Stages/stage5_native_full_results.txt",
    "Stages/stage4_python_results.json",
    "Stages/stage5_python_results.json",
)


def git_output(repository: Path, *arguments: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repository), *arguments], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    repository = arguments.repository.resolve()

    artifacts: dict[str, dict[str, int | str]] = {}
    missing: list[str] = []
    for relative_name in MANIFEST_FILES:
        candidate = repository / relative_name
        if candidate.is_file():
            artifacts[relative_name] = {"sha256": sha256(candidate), "bytes": candidate.stat().st_size}
        else:
            missing.append(relative_name)

    manifest = {
        "project": "AGI Vision Substrate",
        "release_path": "CPU verified substrate",
        "git_commit": git_output(repository, "rev-parse", "HEAD"),
        "git_dirty": git_output(repository, "status", "--porcelain") != "",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "artifacts": artifacts,
        "missing_expected_artifacts": missing,
        "pass": not missing,
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
