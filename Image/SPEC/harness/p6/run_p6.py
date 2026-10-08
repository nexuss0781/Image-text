#!/usr/bin/env python3
"""Build, execute, and record the bounded Phase 6 forward-difference suite."""
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
P4_SOURCE = SPEC / "p4" / "raster_admission.cpp"
P4_HEADER = SPEC / "p4" / "raster_admission.hpp"
P5_SOURCE = SPEC / "p5" / "canonical_raster.cpp"
P5_HEADER = SPEC / "p5" / "canonical_raster.hpp"
P6_SOURCE = SPEC / "p6" / "forward_difference.cpp"
P6_HEADER = SPEC / "p6" / "forward_difference.hpp"
TEST = SPEC / "harness" / "p6" / "test_forward_difference.cpp"
RUNNER = SPEC / "harness" / "p6" / "run_p6.py"
CONTRACT = SPEC / "p6" / "forward_difference_xy_v1.contract.json"
FIXTURES = SPEC / "harness" / "fixtures" / "p6_forward_difference_vectors.json"
CATALOG_PATH = SPEC / "harness" / "case_catalog.json"
PROFILE = SPEC / "profiles" / "general_still_image.proposal.json"
EVIDENCE_SCHEMA = SPEC / "harness" / "p6" / "p6_evidence.schema.json"
OUTPUT = SPEC / "harness" / "results" / "latest.p6.run_evidence.json"
STRICT_FLAGS = ["-std=c++20", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion",
                "-Wsign-conversion", "-Wshadow", "-Werror", "-O2"]
SANITIZER_FLAGS = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]
EXPECTED_TESTS = 13
ALLOWED_LIBS = ("linux-vdso", "ld-linux", "libasan", "libubsan", "libstdc++", "libgcc_s",
                "libc.so", "libm.so", "libpthread.so")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def run(command: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)


def worktree_facts() -> dict[str, str]:
    relative_output = OUTPUT.relative_to(ROOT).as_posix()
    command = ["git", "status", "--porcelain=v1", "--untracked-files=all", "--",
               ".", f":(exclude){relative_output}"]
    status = run(command).stdout
    return {"working_tree_state": "dirty" if status.strip() else "clean",
            "working_tree_status_sha256": sha(status.encode("utf-8"))}


def parse_cases(output: str) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
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
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    bindings = catalog.get("execution_evidence", {}).get("p6", {}).get("test_case_bindings", {})
    expected_pairs = {(test_id, case_id) for case_id, test_ids in bindings.items() for test_id in test_ids}
    started = utc()
    failures: list[str] = []
    builds: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="image-vision-p6-") as tmp:
        tmpdir = Path(tmp)
        for mode, extra in (("normal", []), ("address_undefined_sanitizers", SANITIZER_FLAGS)):
            binary = tmpdir / f"p6-{mode}"
            command = [compiler, *STRICT_FLAGS, *extra, str(P4_SOURCE), str(P5_SOURCE),
                       str(P6_SOURCE), str(TEST), "-o", str(binary)]
            built = run(command)
            if built.returncode:
                failures.append(f"{mode} compile failed: {(built.stderr or built.stdout).strip()[:1024]}")
                builds.append({"mode": mode, "status": "fail", "compile_command": command,
                               "compiler_output": (built.stderr or built.stdout)[-4096:],
                               "elapsed_ms": 0.0, "exit_code": built.returncode,
                               "case_results": [], "stdout": "", "stderr": "",
                               "dynamic_link_dependencies": []})
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
            actual_pairs = {(item["test_id"], item["catalog_case_id"]) for item in cases}
            ok = (tested.returncode == 0 and len(cases) == EXPECTED_TESTS and
                  all(item["status"] == "pass" for item in cases) and summary is not None and
                  summary.group(1) == str(EXPECTED_TESTS) and summary.group(2) == str(EXPECTED_TESTS) and
                  actual_pairs == expected_pairs and len(actual_pairs) == len(cases))
            libs: list[str] = []
            ldd = shutil.which("ldd")
            if ldd:
                linked = run([ldd, str(binary)])
                if linked.returncode:
                    failures.append(f"{mode} dynamic-link audit failed")
                else:
                    libs = [match.group(1) for line in linked.stdout.splitlines()
                            if (match := re.match(r"\s*([^\s]+)", line))]
                    unexpected = [name for name in libs if not Path(name).name.startswith(ALLOWED_LIBS)]
                    if unexpected:
                        failures.append(f"unexpected {mode} linked libraries: {unexpected}")
            if not ok:
                failures.append(f"{mode} tests or exact case bindings failed")
            builds.append({"mode": mode, "status": "pass" if ok else "fail",
                           "compile_command": command, "compiler_output": built.stderr[-4096:],
                           "elapsed_ms": elapsed, "exit_code": tested.returncode,
                           "case_results": cases, "stdout": tested.stdout[-12000:],
                           "stderr": tested.stderr[-8000:], "dynamic_link_dependencies": libs})

    input_paths = (P4_SOURCE, P4_HEADER, P5_SOURCE, P5_HEADER, P6_SOURCE, P6_HEADER,
                   TEST, RUNNER, CONTRACT, FIXTURES, CATALOG_PATH, PROFILE, EVIDENCE_SCHEMA)
    hashes = {path.relative_to(ROOT).as_posix(): file_sha(path) for path in input_paths}
    normal = next((item for item in builds if item["mode"] == "normal"), {})
    sanitizer = next((item for item in builds if item["mode"] == "address_undefined_sanitizers"), {})
    cases = normal.get("case_results", [])
    passed = sum(item.get("status") == "pass" for item in cases) if isinstance(cases, list) else 0
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    evidence = {
        "evidence_version": "0.1.0-draft",
        "phase": "P6",
        "status": "failed" if failures else "finished",
        "phase_completion": "p6_forward_difference_xy_v1_engineering_baseline_profile_proposal_open",
        "started_at": started,
        "finished_at": utc(),
        "commit": run(["git", "rev-parse", "HEAD"]).stdout.strip(),
        **worktree_facts(),
        "scope": {
            "profile_id": profile["profile_id"],
            "profile_status": profile["status"],
            "profile_hash": file_sha(PROFILE),
            "runtime_profile_enabled": False,
            "engineering_candidate_allowlist": ["candidate_forward_difference_xy_v1"],
            "operator_version": "forward-difference-xy-v1",
            "exactly_two_planes": True,
            "regions_enabled": False,
            "patches_enabled": False,
            "token_ids_enabled": False,
            "learning_enabled": False,
            "semantic_recognition_enabled": False,
            "act_reverse_rendering_enabled": False,
            "phase7_started": False,
            "cortex_modified": False,
            "production_approval": False,
        },
        "implementation": {
            "language": "C++20",
            "compiler_path": compiler,
            "compiler_version": run([compiler, "--version"]).stdout.splitlines()[0],
            "strict_flags": STRICT_FLAGS,
            "sanitizer_flags": SANITIZER_FLAGS,
            "source_hashes": hashes,
            "external_dependencies": [],
        },
        "counts": {
            "tests_defined": EXPECTED_TESTS,
            "tests_run_normal": len(cases) if isinstance(cases, list) else 0,
            "tests_passed_normal": passed,
            "tests_failed_normal": (len(cases) - passed) if isinstance(cases, list) else EXPECTED_TESTS,
            "sanitizer_status": sanitizer.get("status", "fail"),
        },
        "case_results": cases,
        "build_runs": builds,
        "failures": failures,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"P6 {evidence['status']}: normal {passed}/{EXPECTED_TESTS}; ASan/UBSan {sanitizer.get('status', 'fail')}")
    print(f"Evidence: {OUTPUT.relative_to(ROOT)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
