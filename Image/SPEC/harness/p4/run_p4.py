#!/usr/bin/env python3
"""Build and run the Phase 4 C++ admission/P5-P6 decode tests; record proposal-only evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
SPEC = ROOT / "Image" / "SPEC"
PROFILE = SPEC / "profiles" / "general_still_image.proposal.json"
SOURCE = SPEC / "p4" / "raster_admission.cpp"
HEADER = SPEC / "p4" / "raster_admission.hpp"
TEST = SPEC / "harness" / "p4" / "test_raster_admission.cpp"
DEFAULT_OUTPUT = SPEC / "harness" / "results" / "latest.p4.run_evidence.json"
BASE_FLAGS = [
    "-std=c++20", "-Wall", "-Wextra", "-Wpedantic", "-Wconversion",
    "-Wsign-conversion", "-Wshadow", "-Werror", "-O2",
]
SANITIZER_FLAGS = ["-fsanitize=address,undefined", "-fno-omit-frame-pointer", "-g"]
EXPECTED_TESTS = 33
STANDARD_LIBRARY_PREFIXES = (
    "linux-vdso", "ld-linux", "libasan", "libubsan", "libstdc++", "libgcc_s",
    "libc.so", "libm.so", "libpthread.so",
)
FORBIDDEN_DEPENDENCY_TOKENS = (
    "opencv", "libpng", "libjpeg", "libtiff", "libwebp", "tensorflow", "torch",
    "onnx", "tflite", "boost", "eigen",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def command_text(command: list[str]) -> str:
    # JSON argv is lossless and avoids shell-quoting ambiguity.
    return json.dumps(command, separators=(",", ":"))


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, env=env, text=True, capture_output=True, check=False)


def git_facts() -> dict[str, str]:
    commit_result = run(["git", "rev-parse", "HEAD"])
    commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"
    status_result = run(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    status = status_result.stdout if status_result.returncode == 0 else "git-status-unavailable"
    return {
        "commit": commit,
        "working_tree_state": "dirty" if status.strip() else "clean",
        "working_tree_status_sha256": sha256_bytes(status.encode("utf-8")),
    }


def test_results(stdout: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for line in stdout.splitlines():
        fields = line.split("\t")
        if len(fields) == 5 and fields[0] == "CASE":
            results.append({
                "test_id": fields[1],
                "status": fields[2],
                "catalog_case_id": fields[3],
                "label": fields[4][:256],
            })
    return results


def linked_libraries(binary: Path) -> tuple[list[str], str]:
    ldd = shutil.which("ldd")
    if not ldd:
        return [], "ldd_unavailable"
    result = run([ldd, str(binary)])
    if result.returncode != 0:
        return [], (result.stderr or result.stdout).strip()[:512]
    names: list[str] = []
    for line in result.stdout.splitlines():
        match = re.match(r"\s*([^\s]+)", line)
        if match:
            names.append(match.group(1))
    return names, "ok"


def audit_headers(paths: tuple[Path, ...]) -> dict[str, Any]:
    includes: list[str] = []
    unexpected: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"^\s*#\s*include\s*([<\"])([^>\"]+)[>\"]", text, re.MULTILINE):
            name = match.group(2)
            includes.append(name)
            if match.group(1) == '"' and name not in {"raster_admission.hpp", "../../p4/raster_admission.hpp"}:
                unexpected.append(f"{path.relative_to(ROOT)}: local include {name}")
            elif match.group(1) == "<" and "/" in name:
                unexpected.append(f"{path.relative_to(ROOT)}: non-standard path include {name}")
    return {"includes": sorted(set(includes)), "unexpected_includes": unexpected}


def run_test_binary(binary: Path, mode: str) -> dict[str, Any]:
    env = os.environ.copy()
    if mode == "address_undefined_sanitizers":
        env["ASAN_OPTIONS"] = "detect_leaks=1:halt_on_error=1"
        env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=1"
    started = time.perf_counter()
    result = subprocess.run([str(binary)], cwd=ROOT, env=env, text=True,
                            capture_output=True, check=False)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    cases = test_results(result.stdout)
    summary = re.search(r"^SUMMARY\t(\d+)\t(\d+)\s*$", result.stdout, re.MULTILINE)
    expected = len(cases) == EXPECTED_TESTS and all(item["status"] == "pass" for item in cases)
    expected = expected and summary is not None and summary.group(1) == str(EXPECTED_TESTS)
    expected = expected and summary.group(2) == str(EXPECTED_TESTS) and result.returncode == 0
    return {
        "mode": mode,
        "status": "pass" if expected else "fail",
        "command": [str(binary)],
        "exit_code": result.returncode,
        "elapsed_ms": elapsed_ms,
        "test_count": len(cases),
        "case_results": cases,
        "stdout": result.stdout[-16000:],
        "stderr": result.stderr[-4000:],
    }


def sanitizer_probe(compiler: str, temporary: Path) -> dict[str, Any]:
    probe_source = temporary / "sanitizer_probe.cpp"
    probe_binary = temporary / "sanitizer_probe"
    probe_source.write_text("int main() { return 0; }\n", encoding="utf-8")
    compile_command = [compiler, "-std=c++20", *SANITIZER_FLAGS,
                       str(probe_source), "-o", str(probe_binary)]
    compiled = run(compile_command)
    if compiled.returncode != 0:
        diagnostic = (compiled.stderr or compiled.stdout).strip()[:1024]
        unsupported = any(token in diagnostic.lower() for token in (
            "unrecognized command-line option", "unsupported option", "cannot find -lasan",
            "cannot find -lubsan", "unsupported argument",
        ))
        return {"status": "unavailable" if unsupported else "fail",
                "compile_command": compile_command, "diagnostic": diagnostic}
    tested = subprocess.run([str(probe_binary)], cwd=ROOT, text=True,
                            capture_output=True, check=False)
    if tested.returncode != 0:
        return {"status": "unavailable", "compile_command": compile_command,
                "diagnostic": (tested.stderr or tested.stdout).strip()[:1024]}
    return {"status": "pass", "compile_command": compile_command, "diagnostic": ""}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="evidence JSON path (default: Image/SPEC/harness/results/latest.p4.run_evidence.json)")
    args = parser.parse_args()
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    compiler = os.environ.get("CXX", "g++")
    compiler_path = shutil.which(compiler)
    started_at = utc_now()
    started_clock = time.perf_counter()
    failures: list[str] = []
    builds: list[dict[str, Any]] = []
    link_audits: dict[str, list[str]] = {}

    if not compiler_path:
        evidence = {"status": "failed", "failure": f"compiler not found: {compiler}"}
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(evidence["failure"], file=sys.stderr)
        return 2
    compiler_path = str(Path(compiler_path).resolve())
    version = run([compiler_path, "--version"])
    target = run([compiler_path, "-dumpmachine"])
    version_line = version.stdout.splitlines()[0] if version.stdout else "unknown compiler"
    header_audit = audit_headers((SOURCE, HEADER, TEST))
    if header_audit["unexpected_includes"]:
        failures.extend(header_audit["unexpected_includes"])
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    if profile.get("status") != "proposal" or profile.get("input", {}).get("encoded_formats") != ["PNM_P5", "PNM_P6"]:
        failures.append("test profile must remain proposal-only with exactly the PNM P5/P6 engineering allowlist")

    with tempfile.TemporaryDirectory(prefix="image-vision-p4-") as temp_name:
        temp = Path(temp_name)
        normal_binary = temp / "p4-admission-normal"
        normal_command = [compiler_path, *BASE_FLAGS, str(SOURCE), str(TEST), "-o", str(normal_binary)]
        normal_build = run(normal_command)
        if normal_build.returncode != 0:
            failures.append("normal C++20 build failed: " + (normal_build.stderr or normal_build.stdout).strip()[:1024])
        else:
            normal_run = run_test_binary(normal_binary, "normal")
            builds.append({"mode": "normal", "status": normal_run["status"],
                           "compile_command": normal_command, "compiler_output": normal_build.stderr[-4096:],
                           "test_run": normal_run})
            libraries, audit_status = linked_libraries(normal_binary)
            link_audits["normal"] = libraries
            if audit_status != "ok":
                failures.append("normal binary dependency inspection failed: " + audit_status)
            forbidden = [name for name in libraries
                         if any(token in name.lower() for token in FORBIDDEN_DEPENDENCY_TOKENS)]
            unexpected = [name for name in libraries
                          if not Path(name).name.startswith(STANDARD_LIBRARY_PREFIXES)]
            if forbidden or unexpected:
                failures.append(f"unexpected normal binary dependencies: {forbidden + unexpected}")
            if normal_run["status"] != "pass":
                failures.append("normal test run failed")

        probe = sanitizer_probe(compiler_path, temp)
        if probe["status"] == "pass":
            sanitized_binary = temp / "p4-admission-asan-ubsan"
            sanitized_command = [compiler_path, *BASE_FLAGS, *SANITIZER_FLAGS,
                                 str(SOURCE), str(TEST), "-o", str(sanitized_binary)]
            sanitized_build = run(sanitized_command)
            if sanitized_build.returncode != 0:
                failures.append("sanitized C++20 build failed: " + (sanitized_build.stderr or sanitized_build.stdout).strip()[:1024])
                builds.append({"mode": "address_undefined_sanitizers", "status": "fail",
                               "compile_command": sanitized_command,
                               "compiler_output": sanitized_build.stderr[-4096:]})
            else:
                sanitized_run = run_test_binary(sanitized_binary, "address_undefined_sanitizers")
                builds.append({"mode": "address_undefined_sanitizers", "status": sanitized_run["status"],
                               "compile_command": sanitized_command, "compiler_output": sanitized_build.stderr[-4096:],
                               "test_run": sanitized_run})
                libraries, audit_status = linked_libraries(sanitized_binary)
                link_audits["address_undefined_sanitizers"] = libraries
                if audit_status != "ok":
                    failures.append("sanitizer binary dependency inspection failed: " + audit_status)
                forbidden = [name for name in libraries
                             if any(token in name.lower() for token in FORBIDDEN_DEPENDENCY_TOKENS)]
                unexpected = [name for name in libraries
                              if not Path(name).name.startswith(STANDARD_LIBRARY_PREFIXES)]
                if forbidden or unexpected:
                    failures.append(f"unexpected sanitizer binary dependencies: {forbidden + unexpected}")
                if sanitized_run["status"] != "pass":
                    failures.append("sanitizer test run failed")
        else:
            builds.append({"mode": "address_undefined_sanitizers", "status": probe["status"],
                           "compile_command": probe.get("compile_command", []),
                           "diagnostic": probe.get("diagnostic", "")})
            if probe["status"] == "fail":
                failures.append("sanitizer capability probe failed: " + probe.get("diagnostic", ""))

    test_runs = [build.get("test_run") for build in builds if "test_run" in build]
    primary_cases = test_runs[0]["case_results"] if test_runs else []
    overall_status = "failed" if failures else (
        "finished" if all(build["status"] == "pass" for build in builds) else "partial"
    )
    facts = git_facts()
    source_hashes = {path.relative_to(ROOT).as_posix(): sha256_file(path)
                     for path in (SOURCE, HEADER, TEST, PROFILE)}
    evidence = {
        "evidence_version": "0.2.0-draft",
        "phase": "P4",
        "status": overall_status,
        "phase_completion": "p4_bounded_pnm_p5_p6_decode_complete_production_profile_open",
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_ms": round((time.perf_counter() - started_clock) * 1000, 3),
        **facts,
        "transition_authorization": {
            "p3_coverage_oracle_acceptance": "user_accepted",
            "p4_start_authorization": "user_authorized",
            "record_id": "D-015",
            "review_model": "user_project_owner_plus_assistant_only; no outside review required",
        },
        "scope": {
            "implemented": "C++20 decoded-raster admission and dependency-free binary Netpbm P5/P6 decode",
            "profile_id": profile["profile_id"],
            "profile_status": profile["status"],
            "profile_hash": sha256_file(PROFILE),
            "profile_usage": "proposal-only-test-ceilings; not production authorization",
            "encoded_formats_enabled": profile["input"]["encoded_formats"],
            "decoder_implemented": True,
            "decoder_security_review": "assistant-reviewed-bounded-parser; ASan-UBSan-tested; no external decoder dependency; not production certification",
            "p5_started": False,
            "cortex_modified": False,
            "observation_or_partial_publication_api": False,
        },
        "implementation": {
            "source_hashes": source_hashes,
            "language": "C++20",
            "compiler_path": compiler_path,
            "compiler_version": version_line,
            "compiler_target": target.stdout.strip() or "unknown",
            "normal_build_flags": BASE_FLAGS,
            "sanitizer_flags": SANITIZER_FLAGS,
            "external_source_dependencies": [],
            "include_audit": header_audit,
            "dynamic_link_dependencies": link_audits,
        },
        "build_runs": builds,
        "case_results": primary_cases,
        "counts": {
            "tests_defined": EXPECTED_TESTS,
            "tests_run_normal": len(test_runs[0]["case_results"]) if test_runs else 0,
            "tests_passed_normal": sum(case["status"] == "pass" for case in primary_cases),
            "tests_failed_normal": sum(case["status"] == "fail" for case in primary_cases),
            "sanitizer_status": next((build["status"] for build in builds
                                      if build["mode"] == "address_undefined_sanitizers"), "unavailable"),
        },
        "failures": failures,
        "limitations": [
            "Decoder support is limited to one binary Netpbm P5 or P6 image with maxval 255; all other formats and sample ranges reject.",
            "The PNM parser uses one bounded header pass and one raster copy; exact payload length is required, so trailing and concatenated images reject.",
            "Animation and multipage payloads are unsupported; no observation assembly, canonicalization, pixel transformation, or feature computation is implemented.",
            "Candidate limits are proposal-only test ceilings, not production limits or approval.",
            "The returned std::span is non-owning; caller must maintain backing storage lifetime and immutability.",
            "No observation assembly, persistent state, canonicalization, pixel transformation, or feature computation is implemented.",
            "Source-level standard-library include and host dynamic-link checks do not certify a production binary or target runtime.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Writing a tracked evidence file can itself change `git status`; bind the
    # final artifact to the resulting path/status set, then rewrite without
    # changing that set again.
    final_facts = git_facts()
    evidence["working_tree_state"] = final_facts["working_tree_state"]
    evidence["working_tree_status_sha256"] = final_facts["working_tree_status_sha256"]
    output_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"P4 evidence: {output_path.relative_to(ROOT) if output_path.is_relative_to(ROOT) else output_path}")
    print(f"P4 status: {overall_status}; cases: {evidence['counts']['tests_passed_normal']}/{EXPECTED_TESTS}; "
          f"ASan/UBSan: {evidence['counts']['sanitizer_status']}")
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    return 0 if overall_status == "finished" else 1


if __name__ == "__main__":
    raise SystemExit(main())
