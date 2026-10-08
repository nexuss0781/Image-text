#!/usr/bin/env python3
"""Build, execute, and record the bounded Phase 8 request-runtime suite."""
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
P8_SOURCE = SPEC / "p8" / "request_runtime.cpp"
P8_HEADER = SPEC / "p8" / "request_runtime.hpp"
TEST = SPEC / "harness" / "p8" / "test_request_runtime.cpp"
RUNNER = SPEC / "harness" / "p8" / "run_p8.py"
CONTRACT = SPEC / "p8" / "single_flight_runtime_v1.contract.json"
BINDINGS = SPEC / "harness" / "p8" / "case_bindings.json"
CATALOG = SPEC / "harness" / "case_catalog.json"
PROFILE = SPEC / "profiles" / "general_still_image.proposal.json"
EVIDENCE_SCHEMA = SPEC / "harness" / "p8" / "p8_evidence.schema.json"
OUTPUT = SPEC / "harness" / "results" / "latest.p8.run_evidence.json"
STRICT_FLAGS = ["-std=c++20", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion",
                "-Wsign-conversion", "-Wshadow", "-Werror", "-O2", "-pthread"]
SANITIZER_FLAGS = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]
EXPECTED_TESTS = 12
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
    excluded = OUTPUT.relative_to(ROOT).as_posix()
    status = run(["git", "status", "--porcelain=v1", "--untracked-files=all", "--",
                  ".", f":(exclude){excluded}"]).stdout
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
    binding_doc = json.loads(BINDINGS.read_text(encoding="utf-8"))
    expected_pairs = {(test_id, case_id) for case_id, test_ids in binding_doc["test_case_bindings"].items()
                      for test_id in test_ids}
    started = utc()
    failures: list[str] = []
    builds: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="image-vision-p8-") as tmp:
        tmpdir = Path(tmp)
        for mode, extra in (("normal", []), ("address_undefined_sanitizers", SANITIZER_FLAGS)):
            binary = tmpdir / f"p8-{mode}"
            command = [compiler, *STRICT_FLAGS, *extra, str(P4_SOURCE), str(P8_SOURCE),
                       str(TEST), "-o", str(binary)]
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
                failures.append(f"{mode} tests or exact P8 case bindings failed")
            builds.append({"mode": mode, "status": "pass" if ok else "fail",
                           "compile_command": command, "compiler_output": built.stderr[-4096:],
                           "elapsed_ms": elapsed, "exit_code": tested.returncode,
                           "case_results": cases, "stdout": tested.stdout[-12000:],
                           "stderr": tested.stderr[-8000:], "dynamic_link_dependencies": libs})

    input_paths = (P4_SOURCE, P4_HEADER, P8_SOURCE, P8_HEADER, TEST, RUNNER, CONTRACT,
                   BINDINGS, CATALOG, PROFILE, EVIDENCE_SCHEMA)
    hashes = {path.relative_to(ROOT).as_posix(): file_sha(path) for path in input_paths}
    normal = next((item for item in builds if item["mode"] == "normal"), {})
    sanitizer = next((item for item in builds if item["mode"] == "address_undefined_sanitizers"), {})
    cases = normal.get("case_results", [])
    passed = sum(item.get("status") == "pass" for item in cases) if isinstance(cases, list) else 0
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    limits = profile["limits"]
    evidence = {
        "evidence_version": "0.1.0-draft",
        "phase": "P8",
        "status": "failed" if failures else "finished",
        "phase_completion": "p8_single_flight_still_request_v1_engineering_slice_profile_proposal_open",
        "started_at": started,
        "finished_at": utc(),
        "commit": run(["git", "rev-parse", "HEAD"]).stdout.strip(),
        **worktree_facts(),
        "scope": {
            "profile_id": profile["profile_id"],
            "profile_status": profile["status"],
            "profile_hash": file_sha(PROFILE),
            "max_in_flight_requests": limits["max_in_flight_requests"],
            "max_queue_depth": limits["max_queue_depth"],
            "deadline_ms": limits["deadline_ms"],
            "max_diagnostic_bytes": limits["max_diagnostic_bytes"],
            "features_enabled": profile["features"]["enabled"],
            "uncertainty_mode": profile["uncertainty"]["mode"],
            "animation_allowed": profile["input"]["allow_animation"],
            "frame_transport_enabled": False,
            "telemetry_sink_enabled": False,
            "observation_publication_enabled": False,
            "named_workload_evidence": False,
            "production_approval": False,
            "cortex_modified": False,
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
    print(f"P8 {evidence['status']}: normal {passed}/{EXPECTED_TESTS}; ASan/UBSan {sanitizer.get('status', 'fail')}")
    print(f"Evidence: {OUTPUT.relative_to(ROOT)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
