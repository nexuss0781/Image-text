#!/usr/bin/env python3
"""Build, execute, and record the bounded Phase 5 identity canonicalization tests."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SPEC = ROOT / "Image" / "SPEC"
SOURCE = SPEC / "p5" / "canonical_raster.cpp"
HEADER = SPEC / "p5" / "canonical_raster.hpp"
P4_SOURCE = SPEC / "p4" / "raster_admission.cpp"
P4_HEADER = SPEC / "p4" / "raster_admission.hpp"
TEST = SPEC / "harness" / "p5" / "test_canonical_raster.cpp"
RUNNER = SPEC / "harness" / "p5" / "run_p5.py"
PROFILE = SPEC / "profiles" / "general_still_image.proposal.json"
OUTPUT = SPEC / "harness" / "results" / "latest.p5.run_evidence.json"
FLAGS = ["-std=c++20", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion",
         "-Wsign-conversion", "-Wshadow", "-Werror", "-O2"]
SAN = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]
EXPECTED = 10
ALLOWED_LIBS = ("linux-vdso", "ld-linux", "libasan", "libubsan", "libstdc++", "libgcc_s", "libc.so", "libm.so", "libpthread.so")

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def file_sha(path: Path) -> str:
    return sha(path.read_bytes())

def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def run(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)

def facts() -> dict[str, str]:
    commit = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    status = run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout
    return {"commit": commit, "working_tree_state": "dirty" if status.strip() else "clean",
            "working_tree_status_sha256": sha(status.encode())}

def parse_cases(output: str) -> list[dict[str, str]]:
    found = []
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) == 5 and fields[0] == "CASE":
            found.append({"test_id": fields[1], "status": fields[2],
                          "catalog_case_id": fields[3], "label": fields[4][:256]})
    return found

def main() -> int:
    compiler = shutil.which(os.environ.get("CXX", "g++"))
    if not compiler:
        raise SystemExit("C++ compiler not found")
    compiler = str(Path(compiler).resolve())
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    started = utc()
    failures: list[str] = []
    builds: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="image-vision-p5-") as tmp:
        tmpdir = Path(tmp)
        for mode, extra in (("normal", []), ("address_undefined_sanitizers", SAN)):
            binary = tmpdir / f"p5-{mode}"
            command = [compiler, *FLAGS, *extra, str(P4_SOURCE), str(SOURCE), str(TEST), "-o", str(binary)]
            built = run(command)
            if built.returncode:
                failures.append(f"{mode} compile failed: {(built.stderr or built.stdout).strip()[:1024]}")
                builds.append({"mode": mode, "status": "fail", "compile_command": command,
                               "compiler_output": built.stderr[-4096:]})
                continue
            env = os.environ.copy()
            if mode != "normal":
                env["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1"
                env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
            begin = time.perf_counter()
            tested = subprocess.run([str(binary)], cwd=ROOT, env=env, text=True,
                                    capture_output=True, check=False)
            elapsed = round((time.perf_counter() - begin) * 1000, 3)
            cases = parse_cases(tested.stdout)
            summary = re.search(r"^SUMMARY\t(\d+)\t(\d+)\s*$", tested.stdout, re.MULTILINE)
            ok = (tested.returncode == 0 and len(cases) == EXPECTED and
                  all(item["status"] == "pass" for item in cases) and summary is not None and
                  summary.group(1) == str(EXPECTED) and summary.group(2) == str(EXPECTED))
            libs: list[str] = []
            ldd = shutil.which("ldd")
            if ldd:
                linked = run([ldd, str(binary)])
                if linked.returncode:
                    failures.append(f"{mode} link audit failed")
                else:
                    libs = [match.group(1) for line in linked.stdout.splitlines()
                            if (match := re.match(r"\s*([^\s]+)", line))]
                    unexpected = [name for name in libs if not Path(name).name.startswith(ALLOWED_LIBS)]
                    if unexpected:
                        failures.append(f"unexpected {mode} linked libraries: {unexpected}")
            if not ok:
                failures.append(f"{mode} tests failed")
            builds.append({"mode": mode, "status": "pass" if ok else "fail",
                           "compile_command": command, "compiler_output": built.stderr[-4096:],
                           "elapsed_ms": elapsed, "exit_code": tested.returncode,
                           "case_results": cases, "stdout": tested.stdout[-8000:],
                           "stderr": tested.stderr[-4000:], "dynamic_link_dependencies": libs})
    hashes = {str(path.relative_to(ROOT)): file_sha(path)
              for path in (SOURCE, HEADER, P4_SOURCE, P4_HEADER, TEST, RUNNER, PROFILE)}
    normal = next((item for item in builds if item["mode"] == "normal"), {})
    sanitizer = next((item for item in builds if item["mode"] == "address_undefined_sanitizers"), {})
    cases = normal.get("case_results", [])
    passed = sum(item.get("status") == "pass" for item in cases) if isinstance(cases, list) else 0
    evidence = {
        "evidence_version": "0.1.0-draft", "phase": "P5",
        "status": "failed" if failures else "finished",
        "phase_completion": "p5_identity_canonical_view_and_geometry_complete_proposal_profile_open",
        "started_at": started, "finished_at": utc(), **facts(),
        "scope": {"profile_id": profile["profile_id"], "profile_status": profile["status"],
                  "profile_hash": file_sha(PROFILE), "profile_usage": "proposal-only-test-ceilings; not production authorization",
                  "operation": "identity-only zero-copy canonical raster view; exact HWC uint8 samples retained",
                  "enabled_channels": ["GRAY", "RGB", "RGBA"], "geometry": "identity-v1; explicit source-to-target pixel-center map and inverse",
                  "p5_started": True, "p6_started": False, "cortex_modified": False,
                  "conversions_enabled": False, "color_inference_enabled": False,
                  "orientation_application_enabled": False, "resize_crop_pad_enabled": False,
                  "alpha_compositing_or_dropping_enabled": False, "production_approval": False},
        "implementation": {"language": "C++20", "compiler_path": compiler,
                            "compiler_version": run([compiler, "--version"]).stdout.splitlines()[0],
                            "strict_flags": FLAGS, "sanitizer_flags": SAN,
                            "source_hashes": hashes, "external_dependencies": []},
        "counts": {"tests_run_normal": len(cases) if isinstance(cases, list) else 0,
                   "tests_passed_normal": passed, "tests_failed_normal": (len(cases) - passed) if isinstance(cases, list) else EXPECTED,
                   "sanitizer_status": sanitizer.get("status", "fail")},
        "case_results": cases, "build_runs": builds, "failures": failures,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"P5 {evidence['status']}: normal {passed}/{EXPECTED}; ASan/UBSan {sanitizer.get('status', 'fail')}")
    print(f"Evidence: {OUTPUT.relative_to(ROOT)}")
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
