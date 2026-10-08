#!/usr/bin/env python3
"""Validate Image/SPEC artifacts and recorded P4/P5/P6/P7 evidence with Python stdlib only.

This checker does not execute the C++ component tests, certify production
dependencies, or establish image/AGI capability.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import math
import os
import platform
import re
import shlex
import struct
import subprocess
import sys
import time
import tomllib
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

SPEC_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SPEC_ROOT.parents[1]
HARNESS_ROOT = SPEC_ROOT / "harness"
CATALOG_PATH = HARNESS_ROOT / "case_catalog.json"
FIXTURE_PATH = HARNESS_ROOT / "fixtures" / "analytic_patterns.json"
PROFILE_PATH = SPEC_ROOT / "profiles" / "fixture_profile.example.json"
PROPOSAL_PROFILE_PATH = SPEC_ROOT / "profiles" / "general_still_image.proposal.json"
OBSERVATION_EXAMPLE_PATH = SPEC_ROOT / "contracts" / "examples" / "image_observation.fixture.json"
ERROR_EXAMPLE_PATH = SPEC_ROOT / "contracts" / "examples" / "image_error.fixture.json"
PAYLOAD_EXAMPLES_PATH = SPEC_ROOT / "contracts" / "examples" / "payload_fixtures.json"
TRACEABILITY_PATH = SPEC_ROOT / "TRACEABILITY.md"
RESULTS_PATH = HARNESS_ROOT / "results"
POST_P4_RESULTS_PATH = RESULTS_PATH / "after-p4"
P4_EVIDENCE_PATH = RESULTS_PATH / "latest.p4.run_evidence.json"
P4_EVIDENCE_SCHEMA_PATH = HARNESS_ROOT / "p4" / "p4_evidence.schema.json"
P5_EVIDENCE_PATH = RESULTS_PATH / "latest.p5.run_evidence.json"
P6_EVIDENCE_PATH = RESULTS_PATH / "latest.p6.run_evidence.json"
P6_EVIDENCE_SCHEMA_PATH = HARNESS_ROOT / "p6" / "p6_evidence.schema.json"
P6_CONTRACT_PATH = SPEC_ROOT / "p6" / "forward_difference_xy_v1.contract.json"
P6_FIXTURE_PATH = HARNESS_ROOT / "fixtures" / "p6_forward_difference_vectors.json"
P7_CONTRACT_PATH = SPEC_ROOT / "p7" / "endpoint_code_fraction_v1.contract.json"
P7_FIXTURE_PATH = HARNESS_ROOT / "fixtures" / "p7_endpoint_code_fraction_vectors.json"
P7_BINDINGS_PATH = HARNESS_ROOT / "p7" / "case_bindings.json"
P7_EVIDENCE_PATH = RESULTS_PATH / "latest.p7.run_evidence.json"
P7_EVIDENCE_SCHEMA_PATH = HARNESS_ROOT / "p7" / "p7_evidence.schema.json"
P8_CONTRACT_PATH = SPEC_ROOT / "p8" / "single_flight_runtime_v1.contract.json"
P8_BINDINGS_PATH = HARNESS_ROOT / "p8" / "case_bindings.json"
P8_EVIDENCE_PATH = RESULTS_PATH / "latest.p8.run_evidence.json"
P8_EVIDENCE_SCHEMA_PATH = HARNESS_ROOT / "p8" / "p8_evidence.schema.json"

SCHEMA_PATHS = (
    SPEC_ROOT / "contracts" / "image_error.schema.json",
    SPEC_ROOT / "contracts" / "image_observation.schema.json",
    SPEC_ROOT / "contracts" / "image_profile.schema.json",
    HARNESS_ROOT / "run_evidence.schema.json",
    P4_EVIDENCE_SCHEMA_PATH,
    P6_EVIDENCE_SCHEMA_PATH,
    P7_EVIDENCE_SCHEMA_PATH,
    P8_EVIDENCE_SCHEMA_PATH,
)
JSON_INPUT_PATHS = (*SCHEMA_PATHS, CATALOG_PATH, FIXTURE_PATH, P6_FIXTURE_PATH, P6_CONTRACT_PATH,
                    P7_FIXTURE_PATH, P7_CONTRACT_PATH, P7_BINDINGS_PATH,
                    P8_CONTRACT_PATH, P8_BINDINGS_PATH,
                    PROFILE_PATH, PROPOSAL_PROFILE_PATH,
                    OBSERVATION_EXAMPLE_PATH, ERROR_EXAMPLE_PATH, PAYLOAD_EXAMPLES_PATH)
SCHEMA_METADATA = {"$schema", "$id", "$ref", "$defs", "$comment", "title", "description", "default"}
SCHEMA_KEYWORDS = {
    "additionalProperties", "anyOf", "const", "enum", "format", "items",
    "maxItems", "maxLength", "maxProperties", "maximum", "minItems",
    "minLength", "minProperties", "minimum", "pattern", "properties",
    "required", "type", "uniqueItems",
}


class CheckError(Exception):
    """A specification-package validation failure."""


def strict_json_loads(text: str) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-standard JSON numeric constant {value}")

    def finite_float(value: str) -> float:
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError(f"non-finite JSON number {value}")
        return parsed

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object member {key!r}")
            result[key] = value
        return result

    return json.loads(text, parse_constant=reject_constant, parse_float=finite_float,
                      object_pairs_hook=unique_object)


def strict_json_load(path: Path) -> Any:
    return strict_json_loads(path.read_text(encoding="utf-8"))


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def json_equal(left: Any, right: Any) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, list):
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_equal(left[k], right[k]) for k in left)
    return left == right


def unique_key(value: Any) -> Any:
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("boolean", value)
    if isinstance(value, (int, float)):
        return ("number", Decimal(str(value)).normalize())
    if isinstance(value, str):
        return ("string", value)
    if isinstance(value, list):
        return ("array", tuple(unique_key(item) for item in value))
    if isinstance(value, dict):
        return ("object", tuple((key, unique_key(value[key])) for key in sorted(value)))
    raise CheckError(f"unsupported JSON value type: {type(value).__name__}")


class SubsetSchemaValidator:
    """Small, explicit validator for the keywords used by this spec package."""

    def __init__(self, root_schema: dict[str, Any]):
        self.root = root_schema

    def resolve(self, pointer: str) -> Any:
        if not pointer.startswith("#/"):
            raise CheckError(f"only local JSON Schema references are supported: {pointer}")
        current: Any = self.root
        for raw_part in pointer[2:].split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            if not isinstance(current, dict) or part not in current:
                raise CheckError(f"unresolved schema reference: {pointer}")
            current = current[part]
        return current

    def validate(self, value: Any, schema: Any, path: str = "$", errors: list[str] | None = None) -> list[str]:
        out = errors if errors is not None else []
        if schema is True:
            return out
        if schema is False:
            out.append(f"{path}: rejected by false schema")
            return out
        if not isinstance(schema, dict):
            out.append(f"{path}: malformed schema node")
            return out

        ref = schema.get("$ref")
        if ref is not None:
            try:
                self.validate(value, self.resolve(ref), path, out)
            except CheckError as exc:
                out.append(f"{path}: {exc}")

        expected_type = schema.get("type")
        if expected_type is not None:
            types = expected_type if isinstance(expected_type, list) else [expected_type]
            def type_matches(kind: str) -> bool:
                if kind == "null": return value is None
                if kind == "boolean": return isinstance(value, bool)
                if kind == "integer": return isinstance(value, int) and not isinstance(value, bool)
                if kind == "number": return isinstance(value, (int, float)) and not isinstance(value, bool)
                if kind == "string": return isinstance(value, str)
                if kind == "array": return isinstance(value, list)
                if kind == "object": return isinstance(value, dict)
                return False
            if not any(type_matches(kind) for kind in types):
                out.append(f"{path}: expected type {expected_type}")
                return out

        if "const" in schema and not json_equal(value, schema["const"]):
            out.append(f"{path}: value does not equal const")
        if "enum" in schema and not any(json_equal(value, option) for option in schema["enum"]):
            out.append(f"{path}: value is not in enum")

        if isinstance(value, dict):
            required = schema.get("required", [])
            for name in required:
                if name not in value:
                    out.append(f"{path}: missing required property {name}")
            properties = schema.get("properties", {})
            for name, child_schema in properties.items():
                if name in value:
                    self.validate(value[name], child_schema, f"{path}.{name}", out)
            additional = schema.get("additionalProperties", True)
            for name, child_value in value.items():
                if name not in properties:
                    if additional is False:
                        out.append(f"{path}: additional property {name} is forbidden")
                    elif isinstance(additional, (dict, bool)):
                        self.validate(child_value, additional, f"{path}.{name}", out)
            if len(value) < schema.get("minProperties", 0):
                out.append(f"{path}: fewer than minProperties")
            if len(value) > schema.get("maxProperties", float("inf")):
                out.append(f"{path}: more than maxProperties")

        if isinstance(value, list):
            if len(value) < schema.get("minItems", 0):
                out.append(f"{path}: fewer than minItems")
            if len(value) > schema.get("maxItems", float("inf")):
                out.append(f"{path}: more than maxItems")
            if schema.get("uniqueItems", False):
                keys = [unique_key(item) for item in value]
                if len(set(keys)) != len(keys):
                    out.append(f"{path}: duplicate items where uniqueItems is true")
            item_schema = schema.get("items")
            if item_schema is not None:
                for index, item in enumerate(value):
                    self.validate(item, item_schema, f"{path}[{index}]", out)

        if isinstance(value, str):
            if len(value) < schema.get("minLength", 0):
                out.append(f"{path}: shorter than minLength")
            if len(value) > schema.get("maxLength", float("inf")):
                out.append(f"{path}: longer than maxLength")
            if "pattern" in schema and re.search(schema["pattern"], value) is None:
                out.append(f"{path}: does not match pattern")
            if schema.get("format") == "date-time":
                try:
                    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    if parsed.tzinfo is None:
                        raise ValueError("timezone required")
                except ValueError:
                    out.append(f"{path}: invalid date-time")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                out.append(f"{path}: below minimum")
            if "maximum" in schema and value > schema["maximum"]:
                out.append(f"{path}: above maximum")

        if "anyOf" in schema:
            branch_success = False
            for option in schema["anyOf"]:
                branch_errors: list[str] = []
                self.validate(value, option, path, branch_errors)
                if not branch_errors:
                    branch_success = True
                    break
            if not branch_success:
                out.append(f"{path}: no anyOf branch matched")
        return out


def check_schema_documents(documents: dict[Path, Any]) -> str:
    ids: set[str] = set()
    for path in SCHEMA_PATHS:
        schema = documents[path]
        if not isinstance(schema, dict):
            raise CheckError(f"schema root is not an object: {path.name}")
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise CheckError(f"unexpected or absent schema dialect: {path.name}")
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str) or not schema_id or schema_id in ids:
            raise CheckError(f"missing or duplicate schema $id: {path.name}")
        ids.add(schema_id)
        validate_schema_shape(schema, path.name)
        validator = SubsetSchemaValidator(schema)
        for pointer in collect_refs(schema):
            validator.resolve(pointer)
    return f"Validated {len(SCHEMA_PATHS)} schema documents, supported-keyword structure, unique IDs, and local references."


def validate_schema_shape(node: Any, label: str, location: str = "$", errors: list[str] | None = None) -> None:
    out = errors if errors is not None else []
    if isinstance(node, bool):
        return
    if not isinstance(node, dict):
        out.append(f"{label}{location}: schema node must be an object or boolean")
        return
    unknown = set(node) - SCHEMA_METADATA - SCHEMA_KEYWORDS
    if unknown:
        out.append(f"{label}{location}: unsupported schema keywords {sorted(unknown)}")
    if "pattern" in node:
        try:
            re.compile(node["pattern"])
        except (TypeError, re.error) as exc:
            out.append(f"{label}{location}: invalid pattern: {exc}")
    for key in ("properties", "$defs"):
        mapping = node.get(key, {})
        if not isinstance(mapping, dict):
            out.append(f"{label}{location}: {key} must be an object")
            continue
        for name, child in mapping.items():
            validate_schema_shape(child, label, f"{location}/{key}/{name}", out)
    for key in ("items", "additionalProperties"):
        if key in node and isinstance(node[key], (dict, bool)):
            validate_schema_shape(node[key], label, f"{location}/{key}", out)
    if "anyOf" in node:
        options = node["anyOf"]
        if not isinstance(options, list) or not options:
            out.append(f"{label}{location}: anyOf must be a non-empty array")
        else:
            for index, child in enumerate(options):
                validate_schema_shape(child, label, f"{location}/anyOf/{index}", out)
    if out and errors is None:
        raise CheckError("; ".join(out[:8]))


def collect_refs(node: Any) -> list[str]:
    refs: list[str] = []
    stack = [node]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            ref = current.get("$ref")
            if ref is not None:
                if not isinstance(ref, str):
                    raise CheckError("schema $ref must be a string")
                refs.append(ref)
            stack.extend(value for key, value in current.items() if key not in SCHEMA_METADATA or key == "$defs")
        elif isinstance(current, list):
            stack.extend(current)
    return refs


def require_valid(value: Any, schema: dict[str, Any], label: str) -> None:
    errors = SubsetSchemaValidator(schema).validate(value, schema)
    if errors:
        raise CheckError(f"{label} failed validation: " + "; ".join(errors[:6]))


def observation_sample() -> dict[str, Any]:
    return strict_json_load(OBSERVATION_EXAMPLE_PATH)


def error_sample() -> dict[str, Any]:
    return strict_json_load(ERROR_EXAMPLE_PATH)


def contract_version_set() -> dict[str, str]:
    return {
        "profile_schema": "0.2.0-draft",
        "observation_schema": "0.3.1-draft",
        "error_schema": "0.2.0-draft",
    }


def validate_profile_semantics(profile: dict[str, Any]) -> None:
    if profile["contract_versions"] != contract_version_set():
        raise CheckError("profile does not bind the exact current draft contract versions")
    if profile["status"] == "approved" and not profile.get("approval_record_id"):
        raise CheckError("approved profile lacks its separate approval-record ID")
    sample_range = profile["input"]["sample_range"]
    if not all(math.isfinite(value) for value in sample_range.values()):
        raise CheckError("sample range must be finite")
    if sample_range["minimum"] > sample_range["maximum"]:
        raise CheckError("sample-range minimum exceeds maximum")
    input_policy = profile["input"]
    animated_policy = input_policy.get("animated_policy")
    if input_policy["allow_animation"]:
        if animated_policy not in {"explicit_frame_selection", "profile_defined"}:
            raise CheckError("animation is enabled without an explicit frame policy")
    elif animated_policy is not None and animated_policy != "reject":
        raise CheckError("disabled animation must not declare an accepting frame policy")
    canonicalization = profile["canonicalization"]
    if canonicalization["alpha_policy"] == "composite_explicit_background":
        if not canonicalization.get("alpha_background"):
            raise CheckError("alpha compositing has no explicit background")
    elif "alpha_background" in canonicalization:
        raise CheckError("alpha background is present when compositing is not selected")
    if profile["complexity"]["quadratic_allowed"] is not False:
        raise CheckError("quadratic work must be prohibited")
    policy = profile["implementation_policy"]
    if policy["ml_libraries_frameworks_allowed"] is not False or policy["quadratic_complexity_allowed"] is not False:
        raise CheckError("profile relaxes a binding implementation prohibition")
    enabled = set(profile["features"]["enabled"])
    proved = {op["operation_id"] for op in profile["complexity"]["operations"] if op.get("proof_id")}
    if not enabled.issubset(proved):
        raise CheckError(f"enabled feature lacks an operation proof: {sorted(enabled - proved)}")


def validate_error_semantics(error: dict[str, Any], error_schema: dict[str, Any]) -> None:
    codes = set(error_schema["properties"]["code"]["enum"])
    if error.get("code") not in codes:
        raise CheckError("error code is not in the versioned catalog")
    if error.get("state_changed") is not False:
        raise CheckError("every error must set state_changed=false")
    if not isinstance(error.get("message"), str) or not error["message"]:
        raise CheckError("error message must be a non-empty safe string")
    if len(error["message"].encode("utf-8")) > 512:
        raise CheckError("error message exceeds the 512-byte runtime limit")
    transient_codes = {"BACKPRESSURE", "DEPENDENCY_UNAVAILABLE"}
    if error.get("retryable") and error.get("code") not in transient_codes:
        raise CheckError("only a transient backpressure/dependency error may be retryable")
    if "retry_after_ms" in error and not (error.get("retryable") and error.get("code") in transient_codes):
        raise CheckError("retry_after_ms is allowed only on an explicitly retryable transient error")


def validate_observation_semantics(
    observation: dict[str, Any], profile: dict[str, Any], payload_fixture_set: dict[str, Any]
) -> None:
    if profile["status"] == "proposal":
        raise CheckError("a proposal profile cannot be activated for observation processing")
    if observation["profile_id"] != profile["profile_id"]:
        raise CheckError("observation profile_id differs from selected profile")
    if observation["provenance"]["profile_id"] != profile["profile_id"]:
        raise CheckError("provenance profile_id differs from selected profile")
    if observation["schema_version"] != profile["contract_versions"]["observation_schema"]:
        raise CheckError("observation schema version differs from profile binding")
    capture_time = observation["source"].get("capture_time")
    if capture_time is not None and not math.isfinite(capture_time["value"]):
        raise CheckError("capture-time value must be finite")
    provenance = observation["provenance"]
    if provenance.get("source_integrity_status") == "externally_attested" and "attestation_ref" not in provenance:
        raise CheckError("externally attested provenance lacks its evidence reference")
    if provenance.get("source_integrity_status") == "checksum_verified":
        if "source_payload_ref" not in observation["source"] and not any(
            key in observation["image"] for key in ("encoded_payload_ref", "source_raster_ref", "canonical_pixels_ref")
        ):
            raise CheckError("checksum-verified provenance has no referenced bytes")

    mode = profile["uncertainty"]["mode"]
    uncertainty = observation.get("uncertainty")
    if mode == "disabled" and uncertainty is not None:
        raise CheckError("uncertainty must be omitted when profile mode is disabled")
    if mode != "disabled" and uncertainty is None:
        raise CheckError("profile requires uncertainty but observation omits it")
    if uncertainty is not None:
        expected_calibration = "calibrated" if mode == "calibrated" else "uncalibrated_fallback"
        if uncertainty["calibration_status"] != expected_calibration:
            raise CheckError("uncertainty calibration status differs from profile mode")
        expected_calibration_id = profile["uncertainty"].get("calibration_profile_id")
        if expected_calibration_id and uncertainty["calibration_profile_id"] != expected_calibration_id:
            raise CheckError("uncertainty calibration profile differs from selected profile")
        if uncertainty["convention"] != "0_is_highest_confidence_1_is_highest_uncertainty":
            raise CheckError("uncertainty convention differs from the ENCODER sidecar contract")
        if uncertainty["granularity"] == "image" and uncertainty["shape"] != [1]:
            raise CheckError("image-level uncertainty must contain exactly one value")
        if uncertainty["calibration_status"] == "calibrated" and "calibration_evidence_ref" not in uncertainty:
            raise CheckError("calibrated uncertainty lacks its evidence reference")
        if uncertainty["granularity"] in {"feature_region", "patch"}:
            if "alignment_id" not in uncertainty or "coordinate_transform_id" not in uncertainty:
                raise CheckError("spatial uncertainty lacks alignment or coordinate-transform identity")
        if uncertainty["calibration_status"] == "uncalibrated_fallback":
            if mode == "uncalibrated_fallback" and not profile["uncertainty"]["production_fallback_approved"]:
                raise CheckError("production fallback is not approved by the profile")

    quality = observation["quality"]
    for indicator in quality["indicators"]:
        if not math.isfinite(indicator["value"]):
            raise CheckError("quality indicator value must be finite")
        if indicator["acceptance_effect"] not in {"descriptive_only", "profile_gate"}:
            raise CheckError("quality indicator must declare its acceptance effect")
        if indicator["scope"] != "image" and "affected_region_ref" not in indicator:
            raise CheckError("spatial quality indicator lacks an affected-region reference")
    if quality["status"] == "accepted_degraded" and not (quality["indicators"] or quality.get("flags")):
        raise CheckError("accepted_degraded requires at least one disclosed degradation indicator or flag")

    image = observation["image"]
    chain = image["transform_chain"]
    if not chain:
        raise CheckError("an observation must record its transform chain")
    prior_frame = image["source_frame_id"]
    prior_width, prior_height = image["source_width"], image["source_height"]
    transform_ids: set[str] = set()
    for step in chain:
        if step["transform_id"] in transform_ids:
            raise CheckError("transform IDs must be unique within an observation")
        transform_ids.add(step["transform_id"])
        if step["source_frame_id"] != prior_frame:
            raise CheckError("transform chain source frame does not match preceding target")
        if (step["source_width"], step["source_height"]) != (prior_width, prior_height):
            raise CheckError("transform chain source dimensions do not match preceding target")
        if step["mapping_direction"] != "source_to_target":
            raise CheckError("transform direction must be explicit source_to_target")
        prior_frame = step["target_frame_id"]
        prior_width, prior_height = step["target_width"], step["target_height"]
        matrix = step.get("matrix_3x3")
        if matrix is not None and not all(math.isfinite(value) for value in matrix):
            raise CheckError("transform matrix contains a non-finite value")
        inverse_matrix = step.get("inverse_matrix_3x3")
        if inverse_matrix is not None and not all(math.isfinite(value) for value in inverse_matrix):
            raise CheckError("inverse transform matrix contains a non-finite value")
        if step["mapping_type"] == "identity":
            identity = [1, 0, 0, 0, 1, 0, 0, 0, 1]
            if (matrix != identity or inverse_matrix != identity or not step["invertible"]
                    or (step["source_width"], step["source_height"]) != (step["target_width"], step["target_height"])):
                raise CheckError("identity transform must preserve dimensions and provide an invertible identity map")
        elif step["mapping_type"] == "affine":
            if matrix is None:
                raise CheckError("affine mapping lacks its forward matrix")
            if step["invertible"] and inverse_matrix is None:
                raise CheckError("invertible affine mapping lacks an inverse matrix")
        elif step["mapping_type"] == "nonlinear":
            if "mapping_payload_ref" not in step:
                raise CheckError("nonlinear mapping lacks its mapping payload")
            if step["invertible"] and "inverse_mapping_payload_ref" not in step:
                raise CheckError("invertible nonlinear mapping lacks its inverse mapping")
    if prior_frame != image["canonical_frame_id"]:
        raise CheckError("transform chain terminal frame differs from canonical frame")
    if (prior_width, prior_height) != (image["canonical_width"], image["canonical_height"]):
        raise CheckError("transform chain terminal dimensions differ from canonical dimensions")
    if chain[-1]["transform_id"] != image["transform_id"]:
        raise CheckError("image transform_id does not resolve to the chain endpoint")

    payloads = payload_fixture_set.get("payloads", [])
    if payload_fixture_set.get("status") != "test_only":
        raise CheckError("synthetic payload fixture set must remain test_only")
    resolved: dict[str, dict[str, Any]] = {}
    for item in payloads:
        ref_id = item["reference_id"]
        if ref_id in resolved:
            raise CheckError(f"duplicate test payload reference ID: {ref_id}")
        raw = base64.b64decode(item["bytes_base64"], validate=True)
        if len(raw) != item["byte_length"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise CheckError(f"test payload length/checksum mismatch: {ref_id}")
        size_by_dtype = {"uint8": 1, "int16": 2, "int32": 4, "float32": 4, "float64": 8}
        count = 1
        for dim in item["shape"]:
            if not isinstance(dim, int) or isinstance(dim, bool) or dim <= 0:
                raise CheckError(f"invalid fixture payload dimension: {ref_id}")
            count *= dim
        if count * size_by_dtype[item["dtype"]] != item["byte_length"]:
            raise CheckError(f"test payload shape/type does not match byte length: {ref_id}")
        resolved[ref_id] = item

    expected_kinds = {
        "image.canonical_pixels_ref": "canonical_raster",
        "image.source_raster_ref": "decoded_raster",
        "image.encoded_payload_ref": "encoded_image",
        "uncertainty.values_ref": "uncertainty_values",
        "uncertainty.valid_mask_ref": "validity_mask",
        "uncertainty.calibration_evidence_ref": "provenance_evidence",
        "provenance.attestation_ref": "provenance_evidence",
    }
    features = observation.get("features")
    enabled_features = set(profile["features"]["enabled"])
    if features is not None:
        if features["profile_id"] != observation["profile_id"]:
            raise CheckError("feature set profile differs from observation profile")
        for feature in features["items"]:
            if feature["feature_id"] not in enabled_features:
                raise CheckError("observation emits a feature not enabled by the selected profile")
    refs: list[tuple[str, dict[str, Any]]] = []
    for key in ("encoded_payload_ref", "source_raster_ref", "canonical_pixels_ref"):
        if key in image:
            refs.append((f"image.{key}", image[key]))
    if uncertainty is not None:
        for key in ("values_ref", "valid_mask_ref", "calibration_evidence_ref"):
            if key in uncertainty:
                refs.append((f"uncertainty.{key}", uncertainty[key]))
    if "attestation_ref" in provenance:
        refs.append(("provenance.attestation_ref", provenance["attestation_ref"]))
    if features is not None:
        for index, feature in enumerate(features["items"]):
            refs.append((f"features.items[{index}].payload_ref", feature["payload_ref"]))
            if "valid_mask_ref" in feature:
                refs.append((f"features.items[{index}].valid_mask_ref", feature["valid_mask_ref"]))
    for path, ref in refs:
        expected = expected_kinds.get(path)
        if path.startswith("features.items[") and path.endswith(".payload_ref"):
            expected = "feature_values"
        elif path.startswith("features.items[") and path.endswith(".valid_mask_ref"):
            expected = "validity_mask"
        if expected is not None and ref["content_kind"] != expected:
            raise CheckError(f"payload content_kind mismatch at {path}")
        if ref["scheme"] == "fixture":
            item = resolved.get(ref["reference_id"])
            if item is None:
                raise CheckError(f"unresolved test payload reference: {ref['reference_id']}")
            for name in ("content_kind", "byte_length", "sha256", "shape", "dtype", "layout", "byte_order"):
                if ref.get(name) != item.get(name):
                    raise CheckError(f"test payload metadata mismatch at {path}.{name}")
    if features is not None:
        for feature in features["items"]:
            if feature["shape"] != feature["payload_ref"]["shape"] or feature["dtype"] != feature["payload_ref"]["dtype"]:
                raise CheckError("feature descriptor shape/dtype differs from its payload reference")
            if feature["coordinate_transform_id"] not in transform_ids:
                raise CheckError("feature coordinate transform does not resolve to the observation transform chain")
    if "visual_tokens" in observation:
        raise CheckError("visual-token output requires a separately versioned profile authorization contract")
    has_image_evidence = any(key in image for key in ("encoded_payload_ref", "source_raster_ref", "canonical_pixels_ref"))
    has_feature_evidence = bool(features and features["items"])
    if not (has_image_evidence or has_feature_evidence):
        raise CheckError("observation has no image, feature, or separately authorized token evidence reference")

    raster_ref = image.get("canonical_pixels_ref")
    if raster_ref is not None:
        channels_by_format = {
            "GRAY_U8": (1, "uint8"), "RGB_U8": (3, "uint8"), "RGBA_U8": (4, "uint8"),
            "GRAY_F32": (1, "float32"), "RGB_F32": (3, "float32"), "RGBA_F32": (4, "float32"),
        }
        expected = channels_by_format.get(image["canonical_pixel_format"])
        if expected is None:
            raise CheckError("fixture checker does not have a typed sample for this canonical pixel format")
        channels, dtype = expected
        expected_shape = [image["canonical_height"], image["canonical_width"], channels]
        if raster_ref["layout"] != "HWC" or raster_ref["shape"] != expected_shape or raster_ref["dtype"] != dtype:
            raise CheckError("canonical raster reference does not match canonical dimensions/format")
    if uncertainty is not None:
        values_ref = uncertainty["values_ref"]
        if values_ref["dtype"] != uncertainty["dtype"] or values_ref["shape"] != uncertainty["shape"]:
            raise CheckError("uncertainty reference dtype/shape differs from its descriptor")
        item = resolved[values_ref["reference_id"]]
        raw = base64.b64decode(item["bytes_base64"], validate=True)
        values = struct.unpack("<" + "f" * (len(raw) // 4), raw)
        if len(values) != math.prod(uncertainty["shape"]):
            raise CheckError("uncertainty value count differs from declared shape")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
            raise CheckError("uncertainty fixture values must be finite and in [0,1]")


def validate_candidate_profile_arithmetic(profile: dict[str, Any]) -> None:
    """Check the proposal's exact arithmetic; this is not an approval or proof review."""
    if profile.get("status") != "proposal":
        raise CheckError("general still-image candidate must remain status=proposal")
    input_policy = profile["input"]
    limits = profile["limits"]
    features = profile["features"]
    if input_policy["decoded_layouts"] != ["HWC"] or input_policy["sample_types"] != ["uint8"]:
        raise CheckError("candidate arithmetic expects tightly packed HWC uint8 input")
    if input_policy["channel_orders"] != ["GRAY", "RGB", "RGBA"]:
        raise CheckError("candidate channel set differs from the documented envelope")
    if input_policy["sample_range"] != {"minimum": 0, "maximum": 255}:
        raise CheckError("candidate sample range differs from uint8 code values")
    if input_policy["allow_strides"] or input_policy["encoded_formats"] != ["PNM_P5", "PNM_P6"]:
        raise CheckError("candidate must remain contiguous, with only the bounded PNM P5/P6 decoder enabled for P4 engineering")
    width = limits["max_width"]
    height = limits["max_height"]
    pixels = limits["max_pixels"]
    channels = limits["max_channels"]
    if width * height != pixels:
        raise CheckError("candidate max_pixels must equal max_width * max_height")
    if channels != 4:
        raise CheckError("candidate max_channels must match the maximum RGBA channel count")
    raster_bytes = pixels * channels  # uint8 has one byte per channel sample.
    if limits["max_decoded_bytes"] != raster_bytes:
        raise CheckError("candidate decoded-byte cap does not equal max_pixels * max_channels")
    if limits["max_intermediate_bytes"] != raster_bytes:
        raise CheckError("candidate intermediate reserve must equal one decoded raster")
    candidate_operation = "candidate_forward_difference_xy_v1"
    operations = {item["operation_id"]: item for item in profile["complexity"]["operations"]}
    if candidate_operation not in operations:
        raise CheckError("candidate forward-difference operation/rationale is missing")
    operation = operations[candidate_operation]
    if operation["variables"] != ["P", "C"] or operation["bounded_parameters"].get("C") != channels:
        raise CheckError("candidate difference complexity variables/bounds are inconsistent")
    decoder_operation = "bounded_pnm_p5_p6_decode_v1"
    if decoder_operation not in operations:
        raise CheckError("bounded P5/P6 decoder complexity rationale is missing")
    decoder_complexity = operations[decoder_operation]
    if (decoder_complexity["variables"] != ["bytes", "P", "C"]
            or decoder_complexity["bounded_parameters"].get("C") != 3):
        raise CheckError("P5/P6 decoder complexity variables/bounds are inconsistent")
    expected_elements = 2 * pixels * channels
    expected_output_bytes = expected_elements * 2  # Two int16 planes: Dx and Dy.
    if limits["max_output_elements"] != expected_elements:
        raise CheckError("candidate output-element cap does not equal 2 * P * C")
    if limits["max_output_bytes"] != expected_output_bytes:
        raise CheckError("candidate output-byte cap does not equal 2 * P * C * sizeof(int16)")
    decoder_work_bound = limits["max_encoded_bytes"] + raster_bytes
    expected_work_bound = max(pixels * channels, decoder_work_bound)
    if limits["max_work_units"] != expected_work_bound:
        raise CheckError("candidate work cap must cover the larger of difference work and encoded-plus-decoded byte work")
    if features["enabled"] or features["max_feature_planes_per_pixel"] != 2:
        raise CheckError("candidate difference planes must remain disabled with a two-plane reserve")
    if features["max_regions"] != 0 or features["max_patch_count"] != 0 or features.get("max_scale_count") != 1:
        raise CheckError("candidate profile must remain identity-only with no regions, patches, or extra scales")
    if limits["max_encoded_bytes"] != 67108864 or limits["max_in_flight_requests"] != 1 or limits["max_queue_depth"] != 0:
        raise CheckError("candidate encoded-input or synchronous admission caps changed")
    if profile["provenance"]["retention"] != "profile_defined":
        raise CheckError("candidate retention must remain explicitly unresolved")


def recompute_difference_fixture(fixture: dict[str, Any]) -> None:
    oracle = fixture.get("oracle_review")
    if not isinstance(oracle, dict) or oracle.get("derived_by") != "assistant_manual_review":
        raise CheckError(f"{fixture.get('id', 'unknown')}: independent manual oracle review is missing")
    if oracle.get("independent_of_implementation") is not True or not oracle.get("derivation"):
        raise CheckError(f"{fixture['id']}: oracle derivation is not independent or documented")
    if oracle.get("expected_fields") != ["expected_dx", "expected_dy"]:
        raise CheckError(f"{fixture['id']}: oracle does not bind both expected output fields")
    comparison = oracle.get("comparison", {})
    if comparison != {"kind": "exact_integer", "absolute_tolerance": 0, "relative_tolerance": 0}:
        raise CheckError(f"{fixture['id']}: integer oracle tolerance must be exact and predeclared")
    height, width, channels = fixture["shape_hwc"]
    raster = fixture["input"]
    if len(raster) != height:
        raise CheckError(f"{fixture['id']}: input height does not match shape_hwc")
    for row in raster:
        if len(row) != width:
            raise CheckError(f"{fixture['id']}: input width does not match shape_hwc")
        for pixel in row:
            if len(pixel) != channels or any(not isinstance(v, int) or isinstance(v, bool) for v in pixel):
                raise CheckError(f"{fixture['id']}: channel count or integer sample mismatch")
    dx: list[list[list[int]]] = []
    dy: list[list[list[int]]] = []
    for y in range(height):
        dx_row: list[list[int]] = []
        dy_row: list[list[int]] = []
        for x in range(width):
            nx = min(x + 1, width - 1)
            ny = min(y + 1, height - 1)
            dx_row.append([raster[y][nx][c] - raster[y][x][c] for c in range(channels)])
            dy_row.append([raster[ny][x][c] - raster[y][x][c] for c in range(channels)])
        dx.append(dx_row)
        dy.append(dy_row)
    if dx != fixture.get("expected_dx") or dy != fixture.get("expected_dy"):
        raise CheckError(f"{fixture['id']}: stored expected differences do not match the declared operator")


def validate_p6_contract_and_fixtures(contract: dict[str, Any], fixture_set: dict[str, Any],
                                      profile: dict[str, Any]) -> str:
    if contract.get("contract_version") != "1.0.0-engineering-proposal" or \
            contract.get("contract_id") != "forward-difference-xy-v1" or \
            contract.get("operator_id") != "candidate_forward_difference_xy_v1":
        raise CheckError("P6 operator contract identity or version is missing")
    if (contract.get("status") != "engineering_proposal_not_production_approval" or
            contract.get("candidate_allowlist") != ["candidate_forward_difference_xy_v1"] or
            contract.get("runtime_profile_enabled") is not False or
            profile.get("status") != "proposal" or profile.get("features", {}).get("enabled") != []):
        raise CheckError("P6 engineering allowlist must remain separate from disabled proposal-profile features")
    operations = {item.get("operation_id"): item for item in profile.get("complexity", {}).get("operations", [])}
    candidate = operations.get("candidate_forward_difference_xy_v1", {})
    if (candidate.get("variables") != ["P", "C"] or
            "O(P*C)" not in candidate.get("time_bound", "") or
            profile.get("features", {}).get("max_feature_planes_per_pixel") != 2):
        raise CheckError("P6 candidate does not match the pre-existing proposal complexity reserve")
    expected_math = {
        "dx": "Dx[y,x,c] = X[y,min(x+1,W-1),c] - X[y,x,c]",
        "dy": "Dy[y,x,c] = X[min(y+1,H-1),x,c] - X[y,x,c]",
        "subtraction_order": "neighbor_minus_current",
        "arithmetic": "exact_signed_integer",
        "value_range_inclusive": [-255, 255],
    }
    if any(contract.get("mathematics", {}).get(key) != value for key, value in expected_math.items()):
        raise CheckError("P6 signed-difference equations, scale, or value range differ from the versioned contract")
    if (contract.get("input", {}).get("layout") != "HWC_tightly_packed" or
            contract.get("input", {}).get("sample_type") != "uint8" or
            contract.get("input", {}).get("channel_orders") != ["GRAY", "RGB", "RGBA"] or
            contract.get("outputs", {}).get("plane_count") != 2 or
            contract.get("outputs", {}).get("dtype") != "int16" or
            contract.get("outputs", {}).get("layout") != "HWC" or
            contract.get("outputs", {}).get("shape_each") != ["H", "W", "C"] or
            contract.get("outputs", {}).get("channel_order") != "preserve_input_order" or
            contract.get("outputs", {}).get("coordinate_mapping", "").startswith("output[y,x,c] maps to the same canonical-input pixel index") is False):
        raise CheckError("P6 input/output layout, channel, plane-count, or dtype contract is inconsistent")
    boundary = contract.get("boundary", {})
    if (boundary.get("rule") != "edge_replication" or boundary.get("terminal_column_dx") != "zero" or
            boundary.get("terminal_row_dy") != "zero" or
            boundary.get("one_row") != "all_dy_zero; dx uses the next or replicated terminal column" or
            boundary.get("one_column") != "all_dx_zero; dy uses the next or replicated terminal row" or
            boundary.get("one_by_one") != "both planes contain only zero"):
        raise CheckError("P6 replicated-edge or degenerate-dimension behavior differs from contract")
    resources = contract.get("resources", {})
    if (resources.get("caller_limits_required") != ["max_pixels", "max_channels", "max_output_elements",
                                                        "max_output_bytes", "max_work_units"] or
            resources.get("output_elements_exact") != "2*P*C" or
            resources.get("output_bytes_exact") != "2*P*C*sizeof(int16)" or
            resources.get("work_units_exact") != "2*P*C" or
            resources.get("declared_work_upper_bound") != "2*P*C" or
            resources.get("time_complexity") != "O(P*C)" or
            resources.get("memory_complexity") != "O(P*C) for exactly two output planes; O(1) auxiliary scratch" or
            resources.get("checked_arithmetic_before_allocation") is not True or
            resources.get("partial_output_on_failure") is not False):
        raise CheckError("P6 checked arithmetic, caller limits, work or atomic-output bound is inconsistent")
    required_exclusions = {"pyramids", "regions", "patches", "partial-region masks", "token IDs",
                           "learning", "semantic recognition", "ACT reverse rendering",
                           "Phase 7 quality, uncertainty, and publication behavior"}
    if set(contract.get("explicit_exclusions", [])) != required_exclusions:
        raise CheckError("P6 must explicitly exclude all non-baseline features and Phase 7")

    if (fixture_set.get("contract_id") != "forward-difference-xy-v1" or
            fixture_set.get("status") != "defined" or fixture_set.get("execution_status") != "not_run" or
            fixture_set.get("oracle_policy", {}).get("independent_of_cpp_implementation") is not True):
        raise CheckError("P6 analytic oracle fixture set must remain independent and definition-only")
    fixtures = fixture_set.get("fixtures", [])
    expected_ids = {"rgb_channel_order_2x2", "rgba_channel_order_and_alpha_2x2",
                    "seeded_rgb_xorshift32_3x4"}
    if {item.get("id") for item in fixtures} != expected_ids:
        raise CheckError("P6 exact RGB/RGBA/seeded oracle fixture set is incomplete or unexpected")
    for fixture in fixtures:
        recompute_difference_fixture(fixture)
        flat = [sample for row in fixture["input"] for pixel in row for sample in pixel]
        if any(not 0 <= sample <= 255 for sample in flat):
            raise CheckError(f"{fixture['id']}: input sample is outside uint8 [0,255]")
        expected_flat = [sample for field in ("expected_dx", "expected_dy")
                         for row in fixture[field] for pixel in row for sample in pixel]
        if any(not -255 <= sample <= 255 for sample in expected_flat):
            raise CheckError(f"{fixture['id']}: output oracle is outside int16 forward-difference range")
    seeded = next(item for item in fixtures if item["id"] == "seeded_rgb_xorshift32_3x4")
    if seeded.get("seed") != "0x6D2B79F5" or seeded.get("generator") != "xorshift32_low_byte_v1":
        raise CheckError("P6 seeded fixture must retain its declared deterministic generator and seed")
    state = int(seeded["seed"], 16)
    generated: list[int] = []
    for _ in range(36):
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= state >> 17
        state ^= (state << 5) & 0xFFFFFFFF
        state &= 0xFFFFFFFF
        generated.append(state & 0xFF)
    seeded_flat = [sample for row in seeded["input"] for pixel in row for sample in pixel]
    if generated != seeded_flat:
        raise CheckError("P6 seeded fixture bytes do not match the declared xorshift32 seed")
    return ("Versioned P6 math/resource contract and independent RGB, RGBA, and seeded exact oracles agree; "
            "the candidate is engineering-allowlisted only and profile.features.enabled remains empty.")


def parse_runtime_invariant_ids(text: str) -> set[str]:
    result: set[str] = set()
    section: int | None = None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(\d+)\.", line)
        if heading:
            section = int(heading.group(1))
            continue
        clause = re.match(r"^(\d+)\.", line)
        if clause and section is not None and 1 <= section <= 8:
            result.add(f"RI-{section:02}.{int(clause.group(1)):02}")
        if section == 9:
            result.update(re.findall(r"\bRI-09\.\d{2}\b", line))
    return result


def check_catalog(catalog: dict[str, Any], traceability: str, invariants_text: str) -> str:
    allowed_statuses = {"defined", "not_run", "pass", "fail", "blocked", "not_applicable"}
    if set(catalog.get("status_values", [])) != allowed_statuses:
        raise CheckError("case catalog status_values differ from the defined lifecycle vocabulary")
    cases = catalog.get("cases")
    package_checks = catalog.get("package_checks")
    if not isinstance(cases, list) or not cases or not isinstance(package_checks, list):
        raise CheckError("catalog must define component cases and package checks")
    known_requirements = set(re.findall(r"^\|\s*(IV-\d{3})\s*\|", traceability, re.MULTILINE))
    expected_requirement_ids = {f"IV-{number:03d}" for number in range(1, 26)}
    if known_requirements != expected_requirement_ids:
        missing = sorted(expected_requirement_ids - known_requirements)
        unexpected = sorted(known_requirements - expected_requirement_ids)
        raise CheckError(f"traceability requirement registry differs from IV-001..IV-025; missing={missing}, unexpected={unexpected}")
    case_ids: set[str] = set()
    case_by_id: dict[str, dict[str, Any]] = {}
    id_pattern = r"[A-Z]+(?:-[A-Z]+)*-[0-9]{3}"
    required_case_fields = {
        "id", "suite", "requirement_ids", "invariant_ids", "purpose", "setup", "expected",
        "complexity_sensitive", "definition_status", "execution_status", "case_kind",
    }
    for case in cases:
        if not isinstance(case, dict):
            raise CheckError("component case entry is not an object")
        if not required_case_fields.issubset(case):
            raise CheckError(f"case lacks required fields: {sorted(required_case_fields - set(case))}")
        case_id = case["id"]
        if not isinstance(case_id, str) or not re.fullmatch(id_pattern, case_id) or case_id in case_ids:
            raise CheckError(f"malformed or duplicate case id: {case_id!r}")
        case_ids.add(case_id)
        case_by_id[case_id] = case
        if case["definition_status"] != "defined" or case["case_kind"] != "image_component":
            raise CheckError(f"{case_id}: component case must be explicitly defined and component-scoped")
        if case["execution_status"] not in {"not_run", "blocked"}:
            raise CheckError(f"{case_id}: component case cannot be credited as executed in the catalog")
        if case["execution_status"] == "blocked" and not case.get("execution_blocker"):
            raise CheckError(f"{case_id}: blocked case lacks its missing-input reason")
        if not case["requirement_ids"] or not set(case["requirement_ids"]).issubset(known_requirements):
            raise CheckError(f"untraceable requirement reference in {case_id}")
        if len(case["invariant_ids"]) != len(set(case["invariant_ids"])):
            raise CheckError(f"duplicate invariant reference in {case_id}")

    package_ids: set[str] = set()
    for item in package_checks:
        required = {"id", "suite", "requirement_ids", "purpose", "setup", "expected", "definition_status", "execution_interface"}
        if not isinstance(item, dict) or not required.issubset(item):
            raise CheckError("package-check definition is missing required fields")
        case_id = item["id"]
        if not isinstance(case_id, str) or not re.fullmatch(id_pattern, case_id) or case_id in case_ids or case_id in package_ids:
            raise CheckError(f"malformed or duplicate package-check ID: {case_id!r}")
        package_ids.add(case_id)
        if item["definition_status"] != "defined" or not item["requirement_ids"]:
            raise CheckError(f"{case_id}: package check must be defined and traceable")
        if not set(item["requirement_ids"]).issubset(known_requirements):
            raise CheckError(f"untraceable requirement reference in {case_id}")

    all_definitions = cases + package_checks
    expected_requirements = {
        requirement: sorted(item["id"] for item in all_definitions if requirement in item["requirement_ids"])
        for requirement in sorted(known_requirements)
    }
    if any(not ids for ids in expected_requirements.values()):
        missing = [key for key, ids in expected_requirements.items() if not ids]
        raise CheckError(f"normative requirements have no executable case definition: {missing}")
    if catalog.get("requirement_coverage") != expected_requirements:
        raise CheckError("machine-readable requirement_coverage is missing, stale, or inconsistent")

    known_invariants = parse_runtime_invariant_ids(invariants_text)
    invariant_clause_counts = {1: 11, 2: 7, 3: 6, 4: 9, 5: 4, 6: 5, 7: 5, 8: 4, 9: 1}
    expected_invariant_ids = {
        f"RI-{section:02d}.{clause:02d}"
        for section, count in invariant_clause_counts.items()
        for clause in range(1, count + 1)
    }
    if known_invariants != expected_invariant_ids:
        missing = sorted(expected_invariant_ids - known_invariants)
        unexpected = sorted(known_invariants - expected_invariants)
        raise CheckError(f"runtime invariant registry differs from the current 52 clauses; missing={missing}, unexpected={unexpected}")
    expected_invariants = {
        invariant: sorted(case["id"] for case in cases if invariant in case["invariant_ids"])
        for invariant in sorted(known_invariants)
    }
    if any(not ids for ids in expected_invariants.values()):
        missing = [key for key, ids in expected_invariants.items() if not ids]
        raise CheckError(f"runtime invariants have no executable case definition: {missing}")
    if catalog.get("invariant_coverage") != expected_invariants:
        raise CheckError("machine-readable invariant_coverage is missing, stale, or inconsistent")
    for case in cases:
        unknown = set(case["invariant_ids"]) - known_invariants
        if unknown:
            raise CheckError(f"{case['id']}: unknown runtime invariant IDs: {sorted(unknown)}")

    section = traceability.split("## Phase 3 executable coverage map", 1)
    if len(section) != 2:
        raise CheckError("TRACEABILITY.md lacks the Phase 3 executable coverage map")
    coverage_text = section[1].split("## Source reconciliation", 1)[0]
    req_text, separator, invariant_text = coverage_text.partition("### Runtime invariant clauses")
    if not separator:
        raise CheckError("TRACEABILITY.md lacks the runtime invariant coverage table")

    def table_map(text: str, prefix: str) -> dict[str, list[str]]:
        mapping: dict[str, list[str]] = {}
        for line in text.splitlines():
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            key_match = re.fullmatch(rf"`({prefix})`", cells[0])
            if not key_match:
                continue
            ids = re.findall(r"`({})`".format(id_pattern), cells[1])
            mapping[key_match.group(1)] = sorted(ids)
        return mapping

    if table_map(req_text, r"IV-\d{3}") != expected_requirements:
        raise CheckError("TRACEABILITY.md requirement table does not exactly match the catalog")
    if table_map(invariant_text, r"RI-\d{2}\.\d{2}") != expected_invariants:
        raise CheckError("TRACEABILITY.md invariant table does not exactly match the catalog")
    counts = {status: sum(item["execution_status"] == status for item in cases) for status in ("not_run", "blocked")}
    return (f"{len(cases)} component definitions; {counts['not_run']} not_run, {counts['blocked']} blocked; "
            f"{len(expected_requirements)} requirements and {len(expected_invariants)} runtime invariants map exhaustively; "
            f"{len(package_checks)} package checks remain distinct from component execution.")


def check_markdown_links() -> str:
    checked = 0
    for path in sorted(SPEC_ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local_target = target.split("#", 1)[0].split("?", 1)[0]
            if not local_target:
                continue
            checked += 1
            resolved = (path.parent / local_target).resolve()
            if not resolved.exists():
                raise CheckError(f"broken local Markdown link in {path.relative_to(REPO_ROOT)}: {target}")
    return f"Resolved {checked} relative Markdown links within Image/SPEC."


def check_policy(profile: dict[str, Any]) -> str:
    if profile["implementation_policy"]["language_boundary"] != "cpp_assembly":
        raise CheckError("implementation language boundary is not cpp_assembly")
    if profile["implementation_policy"]["math_library_policy"] not in {"audited_if_used", "owner_approved_only"}:
        raise CheckError("math-library use is not bounded by an audit policy")
    # Reject obvious pairwise terms over image-scaled populations, not permitted P*C work.
    pair = re.compile(r"\b(P|R|Q)\s*(?:\*|×|\.)\s*(P|R|Q)\b|\b(P|R|Q)\s*(?:\^\s*2|²)\b")
    for operation in profile["complexity"]["operations"]:
        if pair.search(operation["time_bound"]):
            raise CheckError(f"obvious pairwise/quadratic term in {operation['operation_id']}")
        if not operation.get("time_bound") or not operation.get("space_bound") or not operation.get("proof_id"):
            raise CheckError(f"incomplete operation complexity declaration: {operation.get('operation_id')}")
    return "C++/Assembly and audited-math boundary retained; ML/quadratic flags false; fixture operation proofs present."


def dependency_audit() -> tuple[dict[str, Any], str, list[str]]:
    py_files = sorted(HARNESS_ROOT.rglob("*.py"))
    import_roots: set[str] = set()
    parse_errors: list[str] = []
    dynamic_import_sites: list[str] = []
    for path in py_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            parse_errors.append(f"{path.relative_to(REPO_ROOT)}: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                import_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                import_roots.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    dynamic_import_sites.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}: __import__")
                elif (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                      and node.func.value.id == "importlib" and node.func.attr == "import_module"):
                    dynamic_import_sites.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}: importlib.import_module")

    external_imports = sorted(name for name in import_roots if name not in sys.stdlib_module_names)
    manifest_paths = sorted(
        path for path in SPEC_ROOT.rglob("*")
        if path.is_file() and path.name.lower() in {
            "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg",
            "cmakelists.txt", "makefile", "meson.build", "cargo.toml", "package.json",
        }
    )
    manifests = [path.relative_to(REPO_ROOT).as_posix() for path in manifest_paths]
    manifest_hashes = {path.relative_to(REPO_ROOT).as_posix(): sha256_file(path) for path in manifest_paths}
    binary_suffixes = {".so", ".dll", ".dylib", ".a", ".o", ".obj", ".exe", ".bin"}
    binaries = sorted(
        path.relative_to(REPO_ROOT).as_posix()
        for path in HARNESS_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in binary_suffixes
    )
    prohibited_names = re.compile(
        r"\b(?:tensorflow|keras|torch|pytorch|jax|onnxruntime|onnx|scikit[-_]learn|sklearn|mxnet|caffe|transformers|tflite)\b",
        re.IGNORECASE,
    )
    manifest_mentions = sorted({match.group(0).lower() for path in manifest_paths
                                 for match in prohibited_names.finditer(path.read_text(encoding="utf-8"))})
    prohibited = sorted({name for name in import_roots if prohibited_names.fullmatch(name)} | set(manifest_mentions))
    local_manifest_mentions = sorted({
        match.group(0).lower()
        for path in manifest_paths
        for match in prohibited_names.finditer(path.read_text(encoding="utf-8"))
    })
    prohibited_harness = sorted({name for name in import_roots if prohibited_names.fullmatch(name)} |
                                {match.group(0).lower() for path in manifest_paths if path.is_relative_to(SPEC_ROOT)
                                 for match in prohibited_names.finditer(path.read_text(encoding="utf-8"))})
    project_manifest_path = REPO_ROOT / "pyproject.toml"
    project_context: dict[str, Any] = {"path": "pyproject.toml", "sha256": sha256_file(project_manifest_path),
                                      "base_dependencies": [], "optional_ml_groups": [],
                                      "scope_note": "Repository-level context only; not imported or installed by the standalone Image/SPEC checker."}
    try:
        manifest_data = tomllib.loads(project_manifest_path.read_text(encoding="utf-8"))
        project = manifest_data.get("project", {})
        project_context["base_dependencies"] = list(project.get("dependencies", []))
        project_context["optional_ml_groups"] = [
            f"{group}: {dependency}"
            for group, dependencies in project.get("optional-dependencies", {}).items()
            for dependency in dependencies if prohibited_names.search(dependency)
        ]
    except (OSError, tomllib.TOMLDecodeError) as exc:
        parse_errors.append(f"pyproject.toml: {exc}")
    findings = external_imports + prohibited_harness + parse_errors + dynamic_import_sites
    inventory = {
        "audit_scope": "Standalone Image/SPEC Python checker imports and all Image/SPEC local manifests; repository pyproject is recorded as context only",
        "python_files": [path.relative_to(REPO_ROOT).as_posix() for path in py_files],
        "python_import_roots": sorted(import_roots),
        "external_import_roots": external_imports,
        "manifests_found": manifests,
        "manifest_sha256": manifest_hashes,
        "binary_artifacts_found": binaries,
        "prohibited_ml_import_names_found": sorted({name for name in import_roots if prohibited_names.fullmatch(name)}),
        "prohibited_ml_manifest_names_found": local_manifest_mentions,
        "repository_manifest_context": project_context,
        "dynamic_import_sites": dynamic_import_sites,
        "parse_errors": parse_errors,
        "limitations": [
            "The Python harness import closure is audited; its audit does not prove the C++ P4 source or binary dependency closure.",
            "The root pyproject has an unrelated optional ml-cpu TensorFlow extra; it is recorded as repository context and is not part of this isolated standard-library invocation.",
            "The P4 host test build records source includes and dynamic links separately; production target binaries, plugins, and decoder dependencies are not audited.",
        ],
        "harness_dependency_closure_audited": not (external_imports or prohibited_harness or parse_errors or dynamic_import_sites),
        "image_runtime_dependency_graph_audited": False,
        "binary_audited": False,
        "harness_external_dependencies_found": bool(external_imports),
        "ml_libraries_frameworks_found": bool(prohibited_harness),
    }
    inventory["findings"] = findings
    note = ("Python harness scripts use standard-library imports only; that import closure is audited. "
            "A pre-existing optional TensorFlow extra is recorded at repository scope, not used by this command; "
            "the C++ P4 host-build source/link audit is separate and does not certify a production runtime.")
    return inventory, note, findings


def git_commit() -> str:
    try:
        value = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        return value if re.fullmatch(r"[a-fA-F0-9]{7,64}", value) else "0000000"
    except (OSError, subprocess.CalledProcessError):
        return "0000000"


def is_ancestor_commit(commit: str) -> bool:
    if not re.fullmatch(r"[a-fA-F0-9]{7,64}", commit):
        return False
    try:
        return subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                              cwd=REPO_ROOT, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, check=False).returncode == 0
    except OSError:
        return False


def relative_ref(path: Path) -> str:
    return Path(os.path.relpath(path.resolve(), REPO_ROOT.resolve())).as_posix()


def git_worktree_info() -> dict[str, str]:
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL,
        )
        return {
            "state": "dirty" if status.strip() else "clean",
            "status_porcelain_sha256": sha256_bytes(status.encode("utf-8")),
            "status_porcelain": status,
        }
    except (OSError, subprocess.CalledProcessError):
        return {
            "state": "unknown",
            "status_porcelain_sha256": sha256_bytes(b"git-status-unavailable"),
            "status_porcelain": "",
        }


def evidence_input_hashes() -> dict[str, str]:
    paths = set(JSON_INPUT_PATHS) | {
        TRACEABILITY_PATH,
        SPEC_ROOT / "contracts" / "RUNTIME_INVARIANTS.md",
        SPEC_ROOT / "contracts" / "COMPATIBILITY_POLICY.md",
        SPEC_ROOT / "contracts" / "ERROR_CATALOG.md",
        SPEC_ROOT / "harness" / "HARNESS.md",
        Path(__file__).resolve(),
        REPO_ROOT / "pyproject.toml",
        P4_EVIDENCE_PATH,
        P5_EVIDENCE_PATH,
        P6_EVIDENCE_PATH,
        P7_EVIDENCE_PATH,
        P8_EVIDENCE_PATH,
    }
    paths.update(
        path for path in SPEC_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".md", ".json"}
        and RESULTS_PATH not in path.parents
    )
    return {
        path.relative_to(REPO_ROOT).as_posix(): sha256_file(path)
        for path in sorted(paths) if path.is_file()
    }


def peak_rss_bytes() -> int | None:
    try:
        import resource
    except ImportError:
        return None
    try:
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(peak if sys.platform == "darwin" else peak * 1024)
    except (AttributeError, OSError, ValueError):
        return None


def iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def counts_for(results: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "defined": len(results), "executed": len(results),
        "passed": sum(item["status"] == "pass" for item in results),
        "failed": sum(item["status"] == "fail" for item in results),
        "blocked": sum(item["status"] == "blocked" for item in results),
        "not_applicable": sum(item["status"] == "not_applicable" for item in results),
    }


def case_result_digest(item: dict[str, Any]) -> str:
    stable_outcome = {key: item[key] for key in ("case_id", "status", "note", "failure_code") if key in item}
    return sha256_bytes(canonical_json(stable_outcome).encode("utf-8"))


def image_scope_check() -> str:
    try:
        tracked = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD", "--"], cwd=REPO_ROOT,
            text=True, stderr=subprocess.DEVNULL,
        ).splitlines()
        untracked = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard"], cwd=REPO_ROOT,
            text=True, stderr=subprocess.DEVNULL,
        ).splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CheckError(f"cannot establish changed-file scope: {exc}") from exc
    changed = sorted(set(tracked + untracked))
    outside_scope = [path for path in changed if not path.startswith("Image/SPEC/")]
    if outside_scope:
        raise CheckError(f"Image VISION changed files outside Image/SPEC: {outside_scope[:8]}")
    cortex_changes = [path for path in changed if path.startswith("src/Cortex/")]
    if cortex_changes:
        raise CheckError(f"Image VISION must not alter Cortex: {cortex_changes[:8]}")
    native_or_codec_suffixes = {
        ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".s", ".asm",
        ".so", ".dll", ".dylib", ".a", ".o", ".obj", ".onnx", ".tflite", ".pt", ".pth",
    }
    allowed_phase_native_sources = {
        "Image/SPEC/p4/raster_admission.cpp",
        "Image/SPEC/p4/raster_admission.hpp",
        "Image/SPEC/harness/p4/test_raster_admission.cpp",
        "Image/SPEC/p5/canonical_raster.cpp",
        "Image/SPEC/p5/canonical_raster.hpp",
        "Image/SPEC/harness/p5/test_canonical_raster.cpp",
        "Image/SPEC/p6/forward_difference.cpp",
        "Image/SPEC/p6/forward_difference.hpp",
        "Image/SPEC/harness/p6/test_forward_difference.cpp",
        "Image/SPEC/p7/quality_indicator.cpp",
        "Image/SPEC/p7/quality_indicator.hpp",
        "Image/SPEC/harness/p7/test_quality_indicator.cpp",
        "Image/SPEC/p8/request_runtime.cpp",
        "Image/SPEC/p8/request_runtime.hpp",
        "Image/SPEC/harness/p8/test_request_runtime.cpp",
    }
    image_native = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in (REPO_ROOT / "Image").rglob("*")
        if path.is_file() and path.suffix.lower() in native_or_codec_suffixes
        and path.relative_to(REPO_ROOT).as_posix() not in allowed_phase_native_sources
    ]
    if image_native:
        raise CheckError(f"Image contains native/codec artifacts outside the authorized P4/P5/P6/P7/P8 implementation subsets: {image_native[:8]}")
    dependency_manifest_names = {
        "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "cargo.toml",
        "package.json", "cmakelists.txt", "makefile", "meson.build",
    }
    new_image_manifests = [
        path for path in changed
        if path.startswith("Image/") and Path(path).name.lower() in dependency_manifest_names
    ]
    if new_image_manifests:
        raise CheckError(f"Image VISION changes added or edited dependency manifests: {new_image_manifests}")

    return (f"Image scope guard passed: {len(changed)} changed paths are confined to Image/SPEC; "
            "Cortex is unchanged, native source is limited to the authorized P4/P5/P6/P7/P8 implementation subsets, "
            "and no external codec source, binary artifact, or dependency manifest was added.")


def p4_evidence_check(documents: dict[Path, Any]) -> str:
    if not P4_EVIDENCE_PATH.is_file():
        raise CheckError(f"P4 evidence artifact is missing: {P4_EVIDENCE_PATH}")
    evidence = strict_json_load(P4_EVIDENCE_PATH)
    schema = documents[P4_EVIDENCE_SCHEMA_PATH]
    require_valid(evidence, schema, "Phase 4 admission and decode evidence")
    if evidence["phase_completion"] != "p4_bounded_pnm_p5_p6_decode_complete_production_profile_open":
        raise CheckError("P4 evidence must record bounded P5/P6 decode completion without claiming production approval")
    if (evidence["status"] != "finished"
            or evidence["counts"]["tests_passed_normal"] != 33
            or evidence["counts"]["tests_failed_normal"] != 0
            or evidence["counts"]["sanitizer_status"] != "pass"
            or evidence["failures"]):
        raise CheckError("P4 bounded-scope completion requires 33/33 normal and sanitizer passes with no failures")
    if evidence["scope"]["profile_hash"] != sha256_file(PROPOSAL_PROFILE_PATH):
        raise CheckError("P4 evidence profile hash differs from the current proposal profile")
    expected_sources = {
        "Image/SPEC/p4/raster_admission.cpp": SPEC_ROOT / "p4" / "raster_admission.cpp",
        "Image/SPEC/p4/raster_admission.hpp": SPEC_ROOT / "p4" / "raster_admission.hpp",
        "Image/SPEC/harness/p4/test_raster_admission.cpp": HARNESS_ROOT / "p4" / "test_raster_admission.cpp",
        "Image/SPEC/profiles/general_still_image.proposal.json": PROPOSAL_PROFILE_PATH,
    }
    current_hashes = {name: sha256_file(path) for name, path in expected_sources.items()}
    if evidence["implementation"]["source_hashes"] != current_hashes:
        raise CheckError("P4 evidence source/profile hashes do not match current inputs; rerun the P4 tests")
    current_commit = git_commit()
    if evidence["commit"] != current_commit and not is_ancestor_commit(evidence["commit"]):
        raise CheckError("P4 evidence commit is neither the current HEAD nor its ancestor")
    current_worktree = git_worktree_info()
    if current_worktree["state"] == "unknown":
        raise CheckError("cannot establish the current worktree for P4 evidence validation")
    if (evidence["commit"] == current_commit and
            evidence["working_tree_status_sha256"] != current_worktree["status_porcelain_sha256"]):
        raise CheckError("current-commit P4 evidence worktree fingerprint is stale")
    if evidence["transition_authorization"]["record_id"] != "D-015":
        raise CheckError("P4 evidence is not bound to the recorded P4 completion scope")
    if (not evidence["scope"]["decoder_implemented"]
            or evidence["scope"]["encoded_formats_enabled"] != ["PNM_P5", "PNM_P6"]):
        raise CheckError("P4 evidence must claim only the implemented PNM P5/P6 decoder subset")
    if evidence["scope"]["p5_started"] or evidence["scope"]["cortex_modified"]:
        raise CheckError("P4 evidence exceeds its authorized phase or repository boundary")

    catalog = documents[CATALOG_PATH]
    bindings = catalog.get("execution_evidence", {}).get("test_case_bindings", {})
    expected_pairs = {(test_id, case_id) for case_id, test_ids in bindings.items()
                      for test_id in test_ids}
    actual_pairs = {(item["test_id"], item["catalog_case_id"])
                    for item in evidence["case_results"]}
    if len(actual_pairs) != len(evidence["case_results"]) or actual_pairs != expected_pairs:
        raise CheckError("P4 test results do not exactly match the catalog evidence bindings")
    known_catalog_ids = {item["id"] for item in catalog.get("cases", [])}
    if any(case_id not in known_catalog_ids for _, case_id in actual_pairs):
        raise CheckError("P4 evidence refers to an unknown catalog case")
    normal = next((item for item in evidence["build_runs"] if item["mode"] == "normal"), None)
    if normal and "test_run" in normal:
        normal_results = normal["test_run"]["case_results"]
        normal_pairs = {(item["test_id"], item["catalog_case_id"])
                        for item in normal_results}
        if normal_pairs != expected_pairs:
            raise CheckError("normal P4 test-run results differ from the bound case set")
        if evidence["counts"]["tests_run_normal"] != len(normal_pairs):
            raise CheckError("P4 normal test count does not match its results")
        if evidence["counts"]["tests_passed_normal"] != sum(item["status"] == "pass" for item in normal_results):
            raise CheckError("P4 normal passing count does not match its results")
        if evidence["counts"]["tests_failed_normal"] != sum(item["status"] == "fail" for item in normal_results):
            raise CheckError("P4 normal failing count does not match its results")
        if evidence["case_results"] != normal_results:
            raise CheckError("top-level P4 results must match the normal test run")
    sanitizer = next((item for item in evidence["build_runs"]
                      if item["mode"] == "address_undefined_sanitizers"), None)
    if sanitizer and "test_run" in sanitizer:
        sanitizer_results = sanitizer["test_run"]["case_results"]
        sanitizer_pairs = {(item["test_id"], item["catalog_case_id"])
                           for item in sanitizer_results}
        if sanitizer_pairs != expected_pairs:
            raise CheckError("sanitizer P4 test-run results differ from the bound case set")
        if evidence["counts"]["sanitizer_status"] != sanitizer["status"]:
            raise CheckError("P4 sanitizer summary does not match its build result")
    if evidence["status"] == "finished":
        if not normal or normal["status"] != "pass" or not sanitizer or sanitizer["status"] != "pass":
            raise CheckError("finished P4 evidence requires passing normal and sanitizer runs")
        if any(item["status"] != "pass" for item in evidence["case_results"]):
            raise CheckError("finished P4 evidence contains a failing case result")
    return (f"P4 evidence validates against its schema and exact catalog bindings; "
            f"recorded status={evidence['status']}, test cases={len(actual_pairs)}, "
            f"sanitizer status={evidence['counts']['sanitizer_status']}.")


def p5_evidence_check() -> str:
    if not P5_EVIDENCE_PATH.is_file():
        raise CheckError(f"P5 evidence artifact is missing: {P5_EVIDENCE_PATH}")
    evidence = strict_json_load(P5_EVIDENCE_PATH)
    if (evidence.get("phase") != "P5" or evidence.get("status") != "finished" or
            evidence.get("phase_completion") !=
            "p5_identity_canonical_view_and_geometry_complete_proposal_profile_open"):
        raise CheckError("P5 evidence does not record only the bounded identity completion scope")
    profile = strict_json_load(PROPOSAL_PROFILE_PATH)
    scope = evidence.get("scope", {})
    if (profile.get("status") != "proposal" or scope.get("profile_status") != "proposal" or
            scope.get("profile_hash") != sha256_file(PROPOSAL_PROFILE_PATH) or
            scope.get("profile_id") != profile.get("profile_id") or
            scope.get("production_approval") is not False):
        raise CheckError("P5 must remain bound to the current proposal-only profile without production approval")
    if (scope.get("p5_started") is not True or scope.get("p6_started") is not False or
            scope.get("cortex_modified") is not False or
            scope.get("operation") != "identity-only zero-copy canonical raster view; exact HWC uint8 samples retained" or
            any(scope.get(name) is not False for name in (
                "conversions_enabled", "color_inference_enabled", "orientation_application_enabled",
                "resize_crop_pad_enabled", "alpha_compositing_or_dropping_enabled"))):
        raise CheckError("P5 evidence exceeds the identity-only, fail-closed phase boundary")
    counts = evidence.get("counts", {})
    if (counts.get("tests_run_normal") != 10 or counts.get("tests_passed_normal") != 10 or
            counts.get("tests_failed_normal") != 0 or counts.get("sanitizer_status") != "pass" or
            evidence.get("failures")):
        raise CheckError("P5 completion requires 10/10 normal and ASan/UBSan passes with no failures")
    current_commit = git_commit()
    if evidence.get("commit") != current_commit and not is_ancestor_commit(str(evidence.get("commit", ""))):
        raise CheckError("P5 evidence commit is neither the current HEAD nor its ancestor")
    current_worktree = git_worktree_info()
    if current_worktree["state"] == "unknown":
        raise CheckError("cannot establish the current worktree for P5 evidence validation")
    if (evidence.get("commit") == current_commit and
            evidence.get("working_tree_status_sha256") != current_worktree["status_porcelain_sha256"]):
        raise CheckError("current-commit P5 evidence worktree fingerprint is stale")
    implementation = evidence.get("implementation", {})
    if implementation.get("external_dependencies") != [] or "-Werror" not in implementation.get("strict_flags", []):
        raise CheckError("P5 must retain strict C++20 warnings and a dependency-free test build")
    expected_sources = {
        "Image/SPEC/p5/canonical_raster.cpp": SPEC_ROOT / "p5" / "canonical_raster.cpp",
        "Image/SPEC/p5/canonical_raster.hpp": SPEC_ROOT / "p5" / "canonical_raster.hpp",
        "Image/SPEC/p4/raster_admission.cpp": SPEC_ROOT / "p4" / "raster_admission.cpp",
        "Image/SPEC/p4/raster_admission.hpp": SPEC_ROOT / "p4" / "raster_admission.hpp",
        "Image/SPEC/harness/p5/test_canonical_raster.cpp": HARNESS_ROOT / "p5" / "test_canonical_raster.cpp",
        "Image/SPEC/harness/p5/run_p5.py": HARNESS_ROOT / "p5" / "run_p5.py",
        "Image/SPEC/profiles/general_still_image.proposal.json": PROPOSAL_PROFILE_PATH,
    }
    if implementation.get("source_hashes") != {
            name: sha256_file(path) for name, path in expected_sources.items()}:
        raise CheckError("P5 source/profile hashes do not match current inputs; rerun the P5 tests")
    catalog = strict_json_load(CATALOG_PATH)
    bindings = catalog.get("execution_evidence", {}).get("p5", {}).get("test_case_bindings", {})
    expected_pairs = {(test_id, case_id) for case_id, test_ids in bindings.items()
                      for test_id in test_ids}
    results = evidence.get("case_results", [])
    actual_pairs = {(item.get("test_id"), item.get("catalog_case_id")) for item in results}
    if len(actual_pairs) != len(results) or actual_pairs != expected_pairs or len(results) != 10:
        raise CheckError("P5 test results do not exactly match the ten catalog evidence bindings")
    if any(item.get("status") != "pass" for item in results):
        raise CheckError("finished P5 evidence contains a failed case")
    known_cases = {item["id"] for item in catalog.get("cases", [])}
    if any(case_id not in known_cases for _, case_id in actual_pairs):
        raise CheckError("P5 evidence refers to an unknown catalog case")
    runs = {item.get("mode"): item for item in evidence.get("build_runs", [])}
    normal = runs.get("normal", {})
    sanitizer = runs.get("address_undefined_sanitizers", {})
    if normal.get("status") != "pass" or sanitizer.get("status") != "pass":
        raise CheckError("finished P5 evidence requires passing normal and ASan/UBSan builds")
    if normal.get("case_results") != results or sanitizer.get("case_results") != results:
        raise CheckError("P5 normal, sanitizer and top-level test results must match exactly")
    return "P5 evidence validates: 10/10 exact-value and geometry cases pass in strict normal and ASan/UBSan builds."


def p6_evidence_check(documents: dict[Path, Any]) -> str:
    if not P6_EVIDENCE_PATH.is_file():
        raise CheckError(f"P6 evidence artifact is missing: {P6_EVIDENCE_PATH}")
    evidence = strict_json_load(P6_EVIDENCE_PATH)
    require_valid(evidence, documents[P6_EVIDENCE_SCHEMA_PATH], "Phase 6 forward-difference evidence")
    profile = strict_json_load(PROPOSAL_PROFILE_PATH)
    scope = evidence["scope"]
    if (evidence["phase"] != "P6" or evidence["status"] != "finished" or
            evidence["phase_completion"] !=
            "p6_forward_difference_xy_v1_engineering_baseline_profile_proposal_open"):
        raise CheckError("P6 evidence does not record the bounded forward-difference engineering baseline")
    if (profile.get("status") != "proposal" or profile.get("features", {}).get("enabled") != [] or
            scope["profile_status"] != "proposal" or scope["profile_hash"] != sha256_file(PROPOSAL_PROFILE_PATH) or
            scope["profile_id"] != profile.get("profile_id") or scope["runtime_profile_enabled"] is not False or
            scope["engineering_candidate_allowlist"] != ["candidate_forward_difference_xy_v1"] or
            scope["operator_version"] != "forward-difference-xy-v1" or
            scope["exactly_two_planes"] is not True or scope["production_approval"] is not False):
        raise CheckError("P6 evidence must keep the sole candidate proposal-only and runtime-disabled")
    forbidden = ("regions_enabled", "patches_enabled", "token_ids_enabled", "learning_enabled",
                 "semantic_recognition_enabled", "act_reverse_rendering_enabled", "phase7_started",
                 "cortex_modified")
    if any(scope[name] is not False for name in forbidden):
        raise CheckError("P6 evidence exceeds its approved engineering boundary or starts Phase 7")
    if evidence["commit"] != git_commit():
        raise CheckError("P6 evidence commit does not match the current repository HEAD")
    if (evidence["working_tree_state"] not in {"clean", "dirty"} or
            not re.fullmatch(r"[a-fA-F0-9]{64}", evidence["working_tree_status_sha256"])):
        raise CheckError("P6 evidence must retain a valid historical worktree fingerprint")

    expected_sources = {
        "Image/SPEC/p4/raster_admission.cpp": SPEC_ROOT / "p4" / "raster_admission.cpp",
        "Image/SPEC/p4/raster_admission.hpp": SPEC_ROOT / "p4" / "raster_admission.hpp",
        "Image/SPEC/p5/canonical_raster.cpp": SPEC_ROOT / "p5" / "canonical_raster.cpp",
        "Image/SPEC/p5/canonical_raster.hpp": SPEC_ROOT / "p5" / "canonical_raster.hpp",
        "Image/SPEC/p6/forward_difference.cpp": SPEC_ROOT / "p6" / "forward_difference.cpp",
        "Image/SPEC/p6/forward_difference.hpp": SPEC_ROOT / "p6" / "forward_difference.hpp",
        "Image/SPEC/harness/p6/test_forward_difference.cpp": HARNESS_ROOT / "p6" / "test_forward_difference.cpp",
        "Image/SPEC/harness/p6/run_p6.py": HARNESS_ROOT / "p6" / "run_p6.py",
        "Image/SPEC/p6/forward_difference_xy_v1.contract.json": P6_CONTRACT_PATH,
        "Image/SPEC/harness/fixtures/p6_forward_difference_vectors.json": P6_FIXTURE_PATH,
        "Image/SPEC/harness/case_catalog.json": CATALOG_PATH,
        "Image/SPEC/profiles/general_still_image.proposal.json": PROPOSAL_PROFILE_PATH,
        "Image/SPEC/harness/p6/p6_evidence.schema.json": P6_EVIDENCE_SCHEMA_PATH,
    }
    if evidence["implementation"]["source_hashes"] != {
            name: sha256_file(path) for name, path in expected_sources.items()}:
        raise CheckError("P6 source/profile/catalog hashes do not match current inputs; rerun the P6 suite")
    implementation = evidence["implementation"]
    if implementation["external_dependencies"] != [] or "-Werror" not in implementation["strict_flags"]:
        raise CheckError("P6 must retain strict C++20 warnings and a dependency-free build")

    catalog = strict_json_load(CATALOG_PATH)
    bindings = catalog.get("execution_evidence", {}).get("p6", {}).get("test_case_bindings", {})
    expected_pairs = {(test_id, case_id) for case_id, test_ids in bindings.items() for test_id in test_ids}
    results = evidence["case_results"]
    actual_pairs = {(item["test_id"], item["catalog_case_id"]) for item in results}
    if (len(results) != 13 or len(actual_pairs) != len(results) or actual_pairs != expected_pairs or
            any(item["status"] != "pass" for item in results)):
        raise CheckError("P6 results must exactly match all 13 passing Phase 6 catalog bindings")
    known_cases = {item["id"] for item in catalog.get("cases", [])}
    if any(case_id not in known_cases for _, case_id in actual_pairs):
        raise CheckError("P6 evidence refers to an unknown component case")
    counts = evidence["counts"]
    if (counts["tests_defined"] != 13 or counts["tests_run_normal"] != 13 or
            counts["tests_passed_normal"] != 13 or counts["tests_failed_normal"] != 0 or
            counts["sanitizer_status"] != "pass" or evidence["failures"]):
        raise CheckError("P6 completion requires 13/13 normal and ASan/UBSan passes with no failures")
    builds = {item["mode"]: item for item in evidence["build_runs"]}
    if set(builds) != {"normal", "address_undefined_sanitizers"}:
        raise CheckError("P6 evidence must include exactly normal and ASan/UBSan builds")
    for mode, build in builds.items():
        if build["status"] != "pass" or build["case_results"] != results:
            raise CheckError(f"P6 {mode} results differ from the passing top-level test set")
        unexpected = [name for name in build["dynamic_link_dependencies"]
                      if not Path(name).name.startswith(("linux-vdso", "ld-linux", "libasan", "libubsan",
                                                         "libstdc++", "libgcc_s", "libc.so", "libm.so", "libpthread.so"))]
        if unexpected:
            raise CheckError(f"unexpected {mode} dependencies in Phase 6 test binary: {unexpected}")
    return ("P6 evidence validates against its preserved historical source/catalog hashes and recorded worktree fingerprint: "
            "13/13 exact operator, bound, replay and atomicity cases pass in strict normal and ASan/UBSan builds; "
            "production profile remains disabled.")


def p7_contract_check(documents: dict[Path, Any]) -> str:
    contract = documents[P7_CONTRACT_PATH]
    fixture_set = documents[P7_FIXTURE_PATH]
    profile = documents[PROPOSAL_PROFILE_PATH]
    if (contract.get("phase") != "P7" or
            contract.get("contract_version") != "endpoint-code-fraction-v1" or
            contract.get("status") != "engineering_only_profile_proposal_open"):
        raise CheckError("P7 contract must identify only the bounded engineering slice")
    indicator = contract.get("indicator", {})
    if (indicator.get("name") != "endpoint_code_fraction" or
            indicator.get("method_id") != "uint8-endpoint-code-fraction" or
            indicator.get("method_version") != "1" or indicator.get("scope") != "image" or
            indicator.get("units") != "fraction" or
            indicator.get("acceptance_effect") != "descriptive_only" or
            indicator.get("numerator") != "N = count of included samples whose value is exactly 0 or exactly 255" or
            indicator.get("denominator") != "D = P * K, where P = width * height and K is 1 for GRAY, 3 for RGB, and 3 for RGBA" or
            indicator.get("output_payload_bytes") != 24):
        raise CheckError("P7 metric identity, exact counts, descriptive effect, or output bound changed")
    if (indicator.get("included_channels") != {"GRAY": ["GRAY"], "RGB": ["R", "G", "B"],
                                                "RGBA": ["R", "G", "B"]} or
            indicator.get("excluded_channels") != {"GRAY": [], "RGB": [], "RGBA": ["A"]}):
        raise CheckError("P7 color-channel inclusion/exclusion differs from the exact metric contract")
    uncertainty = contract.get("uncertainty", {})
    if (profile.get("status") != "proposal" or profile.get("features", {}).get("enabled") != [] or
            profile.get("uncertainty", {}).get("mode") != "disabled" or
            uncertainty.get("profile_mode") != "disabled" or
            uncertainty.get("default_behavior") != "Omit uncertainty entirely; return no uncertainty values." or
            uncertainty.get("when_explicitly_required") !=
            "Return UNCERTAINTY_UNAVAILABLE with no quality or uncertainty result." or
            uncertainty.get("estimator") != "none" or uncertainty.get("calibration") != "none" or
            uncertainty.get("target_event") != "none" or uncertainty.get("thresholds_or_dataset") != "none"):
        raise CheckError("P7 must keep uncertainty disabled, omitted by default, and unavailable when required")
    if (contract.get("limits", {}).get("caller_supplied_only") is not True or
            contract.get("control", {}).get("persistent_state_api") is not False or
            not contract.get("control", {}).get("atomicity")):
        raise CheckError("P7 must use caller-supplied bounds and declare all-or-nothing, nonpersistent behavior")
    if fixture_set.get("status") != "defined" or fixture_set.get("execution_status") != "not_run":
        raise CheckError("P7 literal fixtures must remain definitions; run outcomes belong in evidence")
    if fixture_set.get("oracle_policy", {}).get("expected_counts_fixed_before_implementation_results") is not True:
        raise CheckError("P7 literal integer expectations must be frozen before implementation results")
    fixtures = fixture_set.get("fixtures", [])
    if len(fixtures) != 4:
        raise CheckError("P7 must retain the four independent literal fixtures")
    for fixture in fixtures:
        layout = fixture.get("layout")
        channels = {"GRAY": 1, "RGB": 3, "RGBA": 3}.get(layout)
        width, height = fixture.get("width"), fixture.get("height")
        if (channels is None or not isinstance(width, int) or isinstance(width, bool) or width <= 0 or
                not isinstance(height, int) or isinstance(height, bool) or height <= 0):
            raise CheckError(f"{fixture.get('id', 'P7 fixture')}: invalid layout or dimensions")
        denominator = width * height * channels
        if "before_samples_hwc" in fixture:
            before, after = fixture["before_samples_hwc"], fixture["after_samples_hwc"]
            if len(before) != width * height or len(after) != width * height:
                raise CheckError("controlled-change GRAY fixture sample count differs from dimensions")
            before_count = sum(value in (0, 255) for value in before)
            after_count = sum(value in (0, 255) for value in after)
            expected = (before_count, after_count, denominator,
                        before_count / denominator, after_count / denominator)
            actual = (fixture.get("before_numerator"), fixture.get("after_numerator"),
                      fixture.get("denominator"), fixture.get("before_value"), fixture.get("after_value"))
            if expected != actual:
                raise CheckError("controlled-change fixture exact counts differ from its sample literals")
        else:
            samples = fixture.get("samples_hwc", [])
            if len(samples) != width * height * (4 if layout == "RGBA" else channels):
                raise CheckError(f"{fixture.get('id', 'P7 fixture')}: HWC literal sample count differs from dimensions")
            included_per_pixel = 4 if layout == "RGBA" else channels
            endpoint_count = 0
            for pixel in range(width * height):
                start = pixel * included_per_pixel
                for channel in range(channels):
                    if samples[start + channel] in (0, 255):
                        endpoint_count += 1
            value = endpoint_count / denominator
            if (fixture.get("numerator") != endpoint_count or fixture.get("denominator") != denominator or
                    fixture.get("value") != value):
                raise CheckError(f"{fixture.get('id', 'P7 fixture')}: endpoint oracle differs from sample literals")
    error_schema = documents[SPEC_ROOT / "contracts" / "image_error.schema.json"]
    schema_codes = set(error_schema["properties"]["code"]["enum"])
    catalog_text = (SPEC_ROOT / "contracts" / "ERROR_CATALOG.md").read_text(encoding="utf-8")
    catalog_codes = set(re.findall(r"\| `([A-Z_]+)` \|", catalog_text))
    implementation_text = (SPEC_ROOT / "p7" / "quality_indicator.cpp").read_text(encoding="utf-8")
    seen_codes: set[str] = set()
    for error in contract.get("errors", []):
        code, message = error.get("code"), error.get("message")
        if (code in seen_codes or code not in schema_codes or code not in catalog_codes or
                error.get("retryable") is not False or not isinstance(message, str) or
                not message or len(message.encode("utf-8")) > 512):
            raise CheckError("P7 error mappings must be unique, catalogued, nonretryable, and bounded")
        seen_codes.add(code)
        enum_name = code.lower()
        if (f'case ErrorCode::{enum_name}: return "{code}";' not in implementation_text or
                f'return "{message}";' not in implementation_text):
            raise CheckError(f"P7 fixed error code/message implementation differs for {code}")
    if "UNCERTAINTY_UNAVAILABLE" not in seen_codes or "INTERNAL_ERROR" not in seen_codes:
        raise CheckError("P7 stable error mapping omits uncertainty or atomic fault failures")
    return "P7 exact metric, channel accounting, literal oracles, proposal-only uncertainty policy, and fixed safe error mappings validate."


def p7_evidence_check(documents: dict[Path, Any]) -> str:
    if not P7_EVIDENCE_PATH.is_file():
        raise CheckError(f"P7 evidence artifact is missing: {P7_EVIDENCE_PATH}")
    evidence = strict_json_load(P7_EVIDENCE_PATH)
    require_valid(evidence, documents[P7_EVIDENCE_SCHEMA_PATH], "Phase 7 quality-indicator evidence")
    profile = documents[PROPOSAL_PROFILE_PATH]
    scope = evidence["scope"]
    if (evidence["phase"] != "P7" or evidence["status"] != "finished" or
            evidence["phase_completion"] !=
            "p7_endpoint_code_fraction_v1_engineering_slice_profile_proposal_open"):
        raise CheckError("P7 evidence does not record the bounded engineering-slice closeout")
    if (profile.get("status") != "proposal" or profile.get("features", {}).get("enabled") != [] or
            profile.get("uncertainty", {}).get("mode") != "disabled" or
            scope["profile_status"] != "proposal" or scope["profile_hash"] != sha256_file(PROPOSAL_PROFILE_PATH) or
            scope["profile_id"] != profile.get("profile_id") or scope["features_enabled"] != [] or
            scope["uncertainty_mode"] != "disabled" or scope["metric"] != "endpoint_code_fraction" or
            scope["metric_enabled_in_profile"] is not False or
            scope["uncertainty_emitted_by_default"] is not False or
            scope["uncertainty_estimator_present"] is not False or
            scope["production_approval"] is not False or scope["phase8_started"] is not False or
            scope["reverse_image_rendering_started"] is not False or scope["cortex_modified"] is not False or
            scope["persistent_state_api"] is not False):
        raise CheckError("P7 evidence exceeds proposal-only, uncertainty-disabled or phase-scope limits")
    if evidence["commit"] != git_commit():
        raise CheckError("P7 evidence commit does not match the current repository HEAD")
    if (evidence["working_tree_state"] not in {"clean", "dirty"} or
            not re.fullmatch(r"[a-fA-F0-9]{64}", evidence["working_tree_status_sha256"])):
        raise CheckError("P7 historical worktree fingerprint is malformed")

    expected_sources = {
        "Image/SPEC/p4/raster_admission.cpp": SPEC_ROOT / "p4" / "raster_admission.cpp",
        "Image/SPEC/p4/raster_admission.hpp": SPEC_ROOT / "p4" / "raster_admission.hpp",
        "Image/SPEC/p5/canonical_raster.cpp": SPEC_ROOT / "p5" / "canonical_raster.cpp",
        "Image/SPEC/p5/canonical_raster.hpp": SPEC_ROOT / "p5" / "canonical_raster.hpp",
        "Image/SPEC/p6/forward_difference.cpp": SPEC_ROOT / "p6" / "forward_difference.cpp",
        "Image/SPEC/p6/forward_difference.hpp": SPEC_ROOT / "p6" / "forward_difference.hpp",
        "Image/SPEC/p7/quality_indicator.cpp": SPEC_ROOT / "p7" / "quality_indicator.cpp",
        "Image/SPEC/p7/quality_indicator.hpp": SPEC_ROOT / "p7" / "quality_indicator.hpp",
        "Image/SPEC/harness/p7/test_quality_indicator.cpp": HARNESS_ROOT / "p7" / "test_quality_indicator.cpp",
        "Image/SPEC/harness/p7/run_p7.py": HARNESS_ROOT / "p7" / "run_p7.py",
        "Image/SPEC/p7/endpoint_code_fraction_v1.contract.json": P7_CONTRACT_PATH,
        "Image/SPEC/harness/fixtures/p7_endpoint_code_fraction_vectors.json": P7_FIXTURE_PATH,
        "Image/SPEC/harness/p7/case_bindings.json": P7_BINDINGS_PATH,
        "Image/SPEC/harness/case_catalog.json": CATALOG_PATH,
        "Image/SPEC/profiles/general_still_image.proposal.json": PROPOSAL_PROFILE_PATH,
        "Image/SPEC/harness/p7/p7_evidence.schema.json": P7_EVIDENCE_SCHEMA_PATH,
    }
    implementation = evidence["implementation"]
    current_hashes = {name: sha256_file(path) for name, path in expected_sources.items()}
    if implementation["source_hashes"] != current_hashes:
        raise CheckError("P7 source/profile/catalog hashes do not match current inputs; rerun P7 tests")
    if (implementation["external_dependencies"] != [] or "-Werror" not in implementation["strict_flags"] or
            "-std=c++20" not in implementation["strict_flags"]):
        raise CheckError("P7 must retain strict C++20 warnings and no external dependencies")

    catalog = documents[CATALOG_PATH]
    bindings_doc = documents[P7_BINDINGS_PATH]
    if bindings_doc.get("phase") != "P7":
        raise CheckError("P7 test bindings must use the separate Phase 7 binding document")
    bindings = bindings_doc.get("test_case_bindings", {})
    expected_pairs = {(test_id, case_id) for case_id, test_ids in bindings.items() for test_id in test_ids}
    expected_ids = {f"P7-TEST-{index:03d}" for index in range(1, 19)}
    results = evidence["case_results"]
    actual_pairs = {(item["test_id"], item["catalog_case_id"]) for item in results}
    known_cases = {item["id"] for item in catalog.get("cases", [])}
    if (len(results) != 18 or len(actual_pairs) != len(results) or actual_pairs != expected_pairs or
            {test_id for test_id, _ in actual_pairs} != expected_ids or
            any(case_id not in known_cases for _, case_id in actual_pairs) or
            any(item["status"] != "pass" for item in results)):
        raise CheckError("P7 results must exactly match all 18 passing, existing-catalog bindings")
    counts = evidence["counts"]
    if (counts["tests_defined"] != 18 or counts["tests_run_normal"] != 18 or
            counts["tests_passed_normal"] != 18 or counts["tests_failed_normal"] != 0 or
            counts["sanitizer_status"] != "pass" or evidence["failures"]):
        raise CheckError("P7 completion requires 18/18 normal and ASan/UBSan passes with no failures")
    builds = {item["mode"]: item for item in evidence["build_runs"]}
    if set(builds) != {"normal", "address_undefined_sanitizers"}:
        raise CheckError("P7 evidence must include exactly normal and ASan/UBSan builds")
    for mode, build in builds.items():
        if build["status"] != "pass" or build["case_results"] != results:
            raise CheckError(f"P7 {mode} results differ from the passing top-level test set")
        unexpected = [name for name in build["dynamic_link_dependencies"]
                      if not Path(name).name.startswith(("linux-vdso", "ld-linux", "libasan", "libubsan",
                                                         "libstdc++", "libgcc_s", "libc.so", "libm.so", "libpthread.so"))]
        if unexpected:
            raise CheckError(f"unexpected {mode} dependencies in Phase 7 test binary: {unexpected}")
    for prior_path in (P4_EVIDENCE_PATH, P5_EVIDENCE_PATH, P6_EVIDENCE_PATH):
        prior = strict_json_load(prior_path).get("implementation", {}).get("source_hashes", {})
        for name, digest in prior.items():
            if name in current_hashes and current_hashes[name] != digest:
                raise CheckError(f"P7 source hash differs from preserved earlier-phase evidence: {name}")
    return "P7 evidence validates against its frozen historical worktree fingerprint and exact source/catalog hashes: 18/18 strict normal and ASan/UBSan cases pass; profile remains proposal-only."


def p8_contract_check(documents: dict[Path, Any]) -> str:
    contract = documents[P8_CONTRACT_PATH]
    profile = documents[PROPOSAL_PROFILE_PATH]
    bindings_doc = documents[P8_BINDINGS_PATH]
    expected_limits = {
        "max_in_flight_requests": 1,
        "max_queue_depth": 0,
        "deadline_ms": 10000,
        "max_diagnostic_bytes": 1024,
    }
    if (contract.get("phase") != "P8" or
            contract.get("contract_version") != "single-flight-still-request-v1" or
            contract.get("status") != "bounded_engineering_slice_profile_proposal_open"):
        raise CheckError("P8 contract must identify only the bounded engineering slice")
    limits = contract.get("limits", {})
    if (profile.get("status") != "proposal" or profile.get("profile_id") !=
            contract.get("scope", {}).get("profile_id") or
            {key: profile.get("limits", {}).get(key) for key in expected_limits} != expected_limits or
            limits.get("proposal_test_ceiling") != expected_limits or
            profile.get("features", {}).get("enabled") != [] or
            profile.get("uncertainty", {}).get("mode") != "disabled" or
            profile.get("input", {}).get("allow_animation") is not False):
        raise CheckError("P8 limits or disabled capability boundary differ from the proposal profile")
    scope = contract.get("scope", {})
    transport = contract.get("frame_transport", {})
    telemetry = contract.get("telemetry", {})
    if (scope.get("profile_status") != "proposal" or scope.get("production_approval") is not False or
            scope.get("features_enabled") != [] or scope.get("uncertainty_mode") != "disabled" or
            scope.get("animation_allowed") is not False or
            scope.get("frame_transport_enabled") is not False or
            scope.get("observation_publication_enabled") is not False or
            scope.get("cortex_modified") is not False or
            transport.get("enabled") is not False or
            transport.get("animation_or_multipage") != "Reject under the unchanged proposal profile." or
            limits.get("diagnostic_bytes_emitted") != 0 or
            telemetry.get("sink") != "No external telemetry sink or logging hook is introduced. Snapshot reads do not alter request results or runtime state."):
        raise CheckError("P8 contract enables an unsupported frame, publication, telemetry, or production capability")
    admission = contract.get("admission", {})
    lifecycle = contract.get("lifecycle", {})
    complexity = contract.get("resources_and_complexity", {})
    if (admission.get("mode") != "nonblocking_try_begin" or
            admission.get("queue") != "No queue exists; queue depth is exactly zero." or
            lifecycle.get("close_modes") != ["drain", "cancel_active_and_drain"] or
            complexity.get("admission_time") != "O(1)" or
            "O(1)" not in complexity.get("admission_auxiliary_space", "")):
        raise CheckError("P8 admission, lifecycle, or complexity contract is incomplete")

    catalog = documents[CATALOG_PATH]
    known_cases = {item["id"] for item in catalog.get("cases", [])}
    if bindings_doc.get("phase") != "P8":
        raise CheckError("P8 tests require a separate Phase 8 binding document")
    bindings = bindings_doc.get("test_case_bindings", {})
    expected_pairs = {(test_id, case_id) for case_id, test_ids in bindings.items()
                      for test_id in test_ids}
    expected_ids = {f"P8-TEST-{index:03d}" for index in range(1, 13)}
    if ({test_id for test_id, _ in expected_pairs} != expected_ids or
            len(expected_pairs) != 12 or any(case_id not in known_cases for _, case_id in expected_pairs)):
        raise CheckError("P8 bindings must map each of 12 unique tests to an existing catalog definition")
    return "P8 single-flight limits, proposal-only boundary, no-frame/no-publication policy, O(1) runtime contract, and exact separate case bindings validate."


def p8_evidence_check(documents: dict[Path, Any]) -> str:
    if not P8_EVIDENCE_PATH.is_file():
        raise CheckError(f"P8 evidence artifact is missing: {P8_EVIDENCE_PATH}")
    evidence = strict_json_load(P8_EVIDENCE_PATH)
    require_valid(evidence, documents[P8_EVIDENCE_SCHEMA_PATH], "Phase 8 request-runtime evidence")
    profile = documents[PROPOSAL_PROFILE_PATH]
    scope = evidence["scope"]
    limits = profile["limits"]
    if (evidence["phase"] != "P8" or evidence["status"] != "finished" or
            evidence["phase_completion"] !=
            "p8_single_flight_still_request_v1_engineering_slice_profile_proposal_open"):
        raise CheckError("P8 evidence does not record the bounded engineering-slice outcome")
    if (profile.get("status") != "proposal" or scope["profile_status"] != "proposal" or
            scope["profile_id"] != profile.get("profile_id") or
            scope["profile_hash"] != sha256_file(PROPOSAL_PROFILE_PATH) or
            any(scope[key] != limits[key] for key in
                ("max_in_flight_requests", "max_queue_depth", "deadline_ms", "max_diagnostic_bytes")) or
            scope["features_enabled"] != [] or scope["uncertainty_mode"] != "disabled" or
            scope["animation_allowed"] is not False or scope["frame_transport_enabled"] is not False or
            scope["telemetry_sink_enabled"] is not False or
            scope["observation_publication_enabled"] is not False or
            scope["named_workload_evidence"] is not False or
            scope["production_approval"] is not False or scope["cortex_modified"] is not False):
        raise CheckError("P8 evidence exceeds the proposal-only single-flight scope")
    if evidence["commit"] != git_commit():
        raise CheckError("P8 evidence commit does not match the current repository HEAD")
    status_command = ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", ".",
                      ":(exclude)Image/SPEC/harness/results/latest.p8.run_evidence.json"]
    try:
        current_status = subprocess.check_output(status_command, cwd=REPO_ROOT, text=True,
                                                 stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CheckError(f"cannot establish the Phase 8 worktree fingerprint: {exc}") from exc
    current_state = "dirty" if current_status.strip() else "clean"
    if (evidence["working_tree_state"] != current_state or
            evidence["working_tree_status_sha256"] != sha256_bytes(current_status.encode("utf-8"))):
        raise CheckError("P8 worktree fingerprint is stale; rerun the Phase 8 suite after source/document changes")

    expected_sources = {
        "Image/SPEC/p4/raster_admission.cpp": SPEC_ROOT / "p4" / "raster_admission.cpp",
        "Image/SPEC/p4/raster_admission.hpp": SPEC_ROOT / "p4" / "raster_admission.hpp",
        "Image/SPEC/p8/request_runtime.cpp": SPEC_ROOT / "p8" / "request_runtime.cpp",
        "Image/SPEC/p8/request_runtime.hpp": SPEC_ROOT / "p8" / "request_runtime.hpp",
        "Image/SPEC/harness/p8/test_request_runtime.cpp": HARNESS_ROOT / "p8" / "test_request_runtime.cpp",
        "Image/SPEC/harness/p8/run_p8.py": HARNESS_ROOT / "p8" / "run_p8.py",
        "Image/SPEC/p8/single_flight_runtime_v1.contract.json": P8_CONTRACT_PATH,
        "Image/SPEC/harness/p8/case_bindings.json": P8_BINDINGS_PATH,
        "Image/SPEC/harness/case_catalog.json": CATALOG_PATH,
        "Image/SPEC/profiles/general_still_image.proposal.json": PROPOSAL_PROFILE_PATH,
        "Image/SPEC/harness/p8/p8_evidence.schema.json": P8_EVIDENCE_SCHEMA_PATH,
    }
    implementation = evidence["implementation"]
    current_hashes = {name: sha256_file(path) for name, path in expected_sources.items()}
    if implementation["source_hashes"] != current_hashes:
        raise CheckError("P8 source/profile/catalog hashes do not match current inputs; rerun P8 tests")
    if (implementation["external_dependencies"] != [] or "-Werror" not in implementation["strict_flags"] or
            "-std=c++20" not in implementation["strict_flags"] or "-pthread" not in implementation["strict_flags"]):
        raise CheckError("P8 must retain strict C++20 warnings, pthread concurrency tests, and no external dependencies")

    bindings = documents[P8_BINDINGS_PATH]["test_case_bindings"]
    expected_pairs = {(test_id, case_id) for case_id, test_ids in bindings.items() for test_id in test_ids}
    expected_ids = {f"P8-TEST-{index:03d}" for index in range(1, 13)}
    results = evidence["case_results"]
    actual_pairs = {(item["test_id"], item["catalog_case_id"]) for item in results}
    known_cases = {item["id"] for item in documents[CATALOG_PATH].get("cases", [])}
    if (len(results) != 12 or len(actual_pairs) != len(results) or actual_pairs != expected_pairs or
            {test_id for test_id, _ in actual_pairs} != expected_ids or
            any(case_id not in known_cases for _, case_id in actual_pairs) or
            any(item["status"] != "pass" for item in results)):
        raise CheckError("P8 results must exactly match all 12 passing separate bindings to existing catalog cases")
    counts = evidence["counts"]
    if (counts["tests_defined"] != 12 or counts["tests_run_normal"] != 12 or
            counts["tests_passed_normal"] != 12 or counts["tests_failed_normal"] != 0 or
            counts["sanitizer_status"] != "pass" or evidence["failures"]):
        raise CheckError("P8 completion requires 12/12 normal and ASan/UBSan passes with no failures")
    builds = {item["mode"]: item for item in evidence["build_runs"]}
    if set(builds) != {"normal", "address_undefined_sanitizers"}:
        raise CheckError("P8 evidence must include exactly normal and ASan/UBSan builds")
    for mode, build in builds.items():
        if build["status"] != "pass" or build["case_results"] != results:
            raise CheckError(f"P8 {mode} results differ from the passing top-level test set")
        unexpected = [name for name in build["dynamic_link_dependencies"]
                      if not Path(name).name.startswith(("linux-vdso", "ld-linux", "libasan", "libubsan",
                                                         "libstdc++", "libgcc_s", "libc.so", "libm.so", "libpthread.so"))]
        if unexpected:
            raise CheckError(f"unexpected {mode} dependencies in Phase 8 test binary: {unexpected}")
    for prior_path in (P4_EVIDENCE_PATH, P5_EVIDENCE_PATH, P6_EVIDENCE_PATH, P7_EVIDENCE_PATH):
        prior = strict_json_load(prior_path).get("implementation", {}).get("source_hashes", {})
        for name, digest in prior.items():
            if name in current_hashes and current_hashes[name] != digest:
                raise CheckError(f"P8 source hash differs from preserved earlier-phase evidence: {name}")
    return "P8 evidence validates: 12/12 single-flight, zero-queue, deadline/cancel, close/drain, and privacy snapshot cases pass in strict normal and ASan/UBSan builds; production workload/profile gates remain open."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=POST_P4_RESULTS_PATH,
                        help="evidence output directory (default: Image/SPEC/harness/results/after-p4; preserves the historical pre-acceptance P3 snapshot)")
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else REPO_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    started_at = iso_utc()
    start_clock = time.perf_counter()
    worktree_info = git_worktree_info()
    input_hashes = evidence_input_hashes()
    documents: dict[Path, Any] = {}
    results: list[dict[str, Any]] = []

    def record(case_id: str, fn: Any) -> None:
        case_start = time.perf_counter()
        try:
            note = fn()
            status = "pass"
        except Exception as exc:  # capture a complete run artifact even on a check failure
            note = f"{type(exc).__name__}: {exc}"
            status = "fail"
        item: dict[str, Any] = {
            "case_id": case_id,
            "status": status,
            "duration_ms": round((time.perf_counter() - case_start) * 1000, 3),
            "note": str(note)[:512],
        }
        item["output_digest"] = case_result_digest(item)
        results.append(item)

    def parse_inputs() -> str:
        for path in JSON_INPUT_PATHS:
            documents[path] = strict_json_load(path)
        return f"Parsed {len(JSON_INPUT_PATHS)} specification/profile/catalog/fixture JSON files with non-standard numeric constants rejected."

    record("SPEC-JSON-001", parse_inputs)

    def strict_json_probe_check() -> str:
        for text in ('{"x": 1, "x": 2}', '{"x": 1e999}'):
            try:
                strict_json_loads(text)
            except ValueError:
                continue
            raise CheckError(f"unsafe JSON input was accepted: {text}")
        return "Duplicate object members and exponent-overflow non-finite numbers reject."

    record("SPEC-JSON-ADVERSARIAL-001", strict_json_probe_check)
    record("SPEC-SCHEMA-001", lambda: check_schema_documents(documents))

    def profile_contract_check() -> str:
        profile_schema = documents[SPEC_ROOT / "contracts" / "image_profile.schema.json"]
        profile = documents[PROFILE_PATH]
        require_valid(profile, profile_schema, "fixture profile")
        validate_profile_semantics(profile)
        invalid = json.loads(canonical_json(profile))
        invalid["input"]["sample_range"]["minimum"] = 256
        invalid["input"]["sample_range"]["maximum"] = 0
        try:
            validate_profile_semantics(invalid)
        except CheckError:
            pass
        else:
            raise CheckError("negative cross-field sample-range check was not rejected")
        invalid_animation = json.loads(canonical_json(profile))
        invalid_animation["input"]["animated_policy"] = "explicit_frame_selection"
        try:
            validate_profile_semantics(invalid_animation)
        except CheckError:
            pass
        else:
            raise CheckError("disabled animation with an accepting policy was not rejected")
        invalid_alpha = json.loads(canonical_json(profile))
        invalid_alpha["canonicalization"]["alpha_background"] = [255, 255, 255, 255]
        try:
            validate_profile_semantics(invalid_alpha)
        except CheckError:
            pass
        else:
            raise CheckError("alpha background without compositing policy was not rejected")
        extra = json.loads(canonical_json(profile))
        extra["unexpected_property"] = True
        if not SubsetSchemaValidator(profile_schema).validate(extra, profile_schema):
            raise CheckError("negative additional-property check was not rejected")
        return "Fixture profile conforms; cross-field and forbidden-field negative probes reject as expected."

    record("SPEC-PROFILE-001", profile_contract_check)

    def proposal_profile_check() -> str:
        profile_schema = documents[SPEC_ROOT / "contracts" / "image_profile.schema.json"]
        profile = documents[PROPOSAL_PROFILE_PATH]
        require_valid(profile, profile_schema, "general still-image candidate profile")
        validate_profile_semantics(profile)
        validate_candidate_profile_arithmetic(profile)
        return ("Proposal profile conforms; width/pixel, decoded/intermediate bytes, "
                "difference elements/output bytes, work units, and disabled-feature reserves agree.")

    record("SPEC-PROPOSAL-001", proposal_profile_check)

    def observation_error_check() -> str:
        observation_schema = documents[SPEC_ROOT / "contracts" / "image_observation.schema.json"]
        error_schema = documents[SPEC_ROOT / "contracts" / "image_error.schema.json"]
        profile_schema = documents[SPEC_ROOT / "contracts" / "image_profile.schema.json"]
        observation = observation_sample()
        require_valid(observation, observation_schema, "synthetic observation envelope")
        fixture_profile = documents[PROFILE_PATH]
        require_valid(fixture_profile, profile_schema, "fixture profile")
        validate_observation_semantics(observation, fixture_profile, documents[PAYLOAD_EXAMPLES_PATH])
        invalid_observation = json.loads(canonical_json(observation))
        invalid_observation["image"]["source_width"] = 0
        if not SubsetSchemaValidator(observation_schema).validate(invalid_observation, observation_schema):
            raise CheckError("negative observation dimension probe was not rejected")
        unsupported_version = dict(observation, schema_version="9.9.9")
        if not SubsetSchemaValidator(observation_schema).validate(unsupported_version, observation_schema):
            raise CheckError("unsupported observation schema version was not rejected")
        unknown_field = dict(observation, unregistered_field=True)
        if not SubsetSchemaValidator(observation_schema).validate(unknown_field, observation_schema):
            raise CheckError("unknown observation field was not rejected")
        no_evidence = json.loads(canonical_json(observation))
        no_evidence["image"].pop("canonical_pixels_ref")
        no_evidence["provenance"]["source_integrity_status"] = "not_attested"
        no_evidence.setdefault("features", {"profile_id": observation["profile_id"], "items": []})
        if not SubsetSchemaValidator(observation_schema).validate(no_evidence, observation_schema):
            raise CheckError("observation without any evidence reference was not rejected by schema")
        try:
            validate_observation_semantics(no_evidence, fixture_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("observation without any evidence reference was not rejected at runtime")
        broken_chain = json.loads(canonical_json(observation))
        broken_chain["image"]["transform_chain"][0]["source_frame_id"] = "wrong-frame"
        try:
            validate_observation_semantics(broken_chain, fixture_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("cross-field transform frame mismatch was not rejected")
        affine_without_matrix = json.loads(canonical_json(observation))
        affine_without_matrix["image"]["transform_chain"][0]["mapping_type"] = "affine"
        affine_without_matrix["image"]["transform_chain"][0].pop("matrix_3x3")
        affine_without_matrix["image"]["transform_chain"][0].pop("inverse_matrix_3x3")
        try:
            validate_observation_semantics(affine_without_matrix, fixture_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("affine transform without a forward matrix was not rejected")
        nonlinear_without_map = json.loads(canonical_json(observation))
        nonlinear_without_map["image"]["transform_chain"][0]["mapping_type"] = "nonlinear"
        nonlinear_without_map["image"]["transform_chain"][0].pop("matrix_3x3")
        nonlinear_without_map["image"]["transform_chain"][0].pop("inverse_matrix_3x3")
        try:
            validate_observation_semantics(nonlinear_without_map, fixture_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("nonlinear transform without mapping payload was not rejected")
        unapproved_feature = json.loads(canonical_json(observation))
        unapproved_feature["features"] = {
            "profile_id": fixture_profile["profile_id"],
            "items": [{"feature_id": "not-enabled-by-profile"}],
        }
        try:
            validate_observation_semantics(unapproved_feature, fixture_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("feature not enabled by selected profile was not rejected")
        unattested = json.loads(canonical_json(observation))
        unattested["provenance"]["source_integrity_status"] = "externally_attested"
        try:
            validate_observation_semantics(unattested, fixture_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("external attestation without evidence was not rejected")
        wrong_raster_shape = json.loads(canonical_json(observation))
        wrong_raster_shape["image"]["canonical_pixels_ref"]["shape"] = [1, 1, 3]
        try:
            validate_observation_semantics(wrong_raster_shape, fixture_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("canonical raster shape mismatch was not rejected")
        corrupted_fixture = json.loads(canonical_json(documents[PAYLOAD_EXAMPLES_PATH]))
        corrupted_fixture["payloads"][0]["bytes_base64"] = "AQ=="
        try:
            validate_observation_semantics(observation, fixture_profile, corrupted_fixture)
        except CheckError:
            pass
        else:
            raise CheckError("tampered fixture bytes were not rejected")
        disabled_uncertainty = json.loads(canonical_json(observation))
        disabled_profile = json.loads(canonical_json(fixture_profile))
        disabled_profile["profile_id"] = "image-fixture-no-uncertainty-v1"
        disabled_profile["uncertainty"]["mode"] = "disabled"
        disabled_uncertainty["profile_id"] = disabled_profile["profile_id"]
        disabled_uncertainty["provenance"]["profile_id"] = disabled_profile["profile_id"]
        disabled_uncertainty.pop("uncertainty")
        validate_observation_semantics(disabled_uncertainty, disabled_profile, documents[PAYLOAD_EXAMPLES_PATH])
        forbidden_uncertainty = json.loads(canonical_json(disabled_uncertainty))
        forbidden_uncertainty["uncertainty"] = observation["uncertainty"]
        try:
            validate_observation_semantics(forbidden_uncertainty, disabled_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("uncertainty in a disabled profile was not rejected")
        proposal_activation = json.loads(canonical_json(observation))
        proposal_profile = json.loads(canonical_json(documents[PROPOSAL_PROFILE_PATH]))
        proposal_activation["profile_id"] = proposal_profile["profile_id"]
        proposal_activation["provenance"]["profile_id"] = proposal_profile["profile_id"]
        proposal_activation.pop("uncertainty")
        try:
            validate_observation_semantics(proposal_activation, proposal_profile, documents[PAYLOAD_EXAMPLES_PATH])
        except CheckError:
            pass
        else:
            raise CheckError("proposal profile activation was not rejected")
        error = error_sample()
        require_valid(error, error_schema, "synthetic error envelope")
        validate_error_semantics(error, error_schema)
        invalid_error = dict(error, state_changed=True)
        if not SubsetSchemaValidator(error_schema).validate(invalid_error, error_schema):
            raise CheckError("negative error-atomicity probe was not rejected")
        invalid_retry = dict(error, retryable=True)
        try:
            validate_error_semantics(invalid_retry, error_schema)
        except CheckError:
            pass
        else:
            raise CheckError("non-transient retryable error was not rejected")
        catalog_text = (SPEC_ROOT / "contracts" / "ERROR_CATALOG.md").read_text(encoding="utf-8")
        catalog_codes = set(re.findall(r"\| `([A-Z_]+)` \|", catalog_text))
        if catalog_codes != set(error_schema["properties"]["code"]["enum"]):
            raise CheckError("error catalog and schema code sets differ")
        return ("Test-only observation/profile/error records validate; fixture bytes resolve by digest; "
                "version, evidence, profile/feature authorization, transform, disabled-uncertainty, atomicity, and retry probes reject.")

    record("SPEC-CONTRACT-001", observation_error_check)

    def fixture_check() -> str:
        fixture_set = documents[FIXTURE_PATH]
        if fixture_set.get("status") != "defined" or fixture_set.get("execution_status") != "not_run":
            raise CheckError("analytic fixtures must be defined without claiming component execution")
        oracle_policy = fixture_set.get("oracle_policy", {})
        if oracle_policy.get("expected_values_fixed_before_implementation_results") is not True:
            raise CheckError("analytic fixture oracle policy does not freeze expected values before implementation results")
        if "no external reviewer" not in oracle_policy.get("review_model", ""):
            raise CheckError("fixture review model must remain user/project-owner plus assistant only")
        fixtures = fixture_set.get("fixtures", [])
        if not fixtures:
            raise CheckError("analytic fixture set is empty")
        seen: set[str] = set()
        for fixture in fixtures:
            if fixture["id"] in seen:
                raise CheckError(f"duplicate analytic fixture id: {fixture['id']}")
            seen.add(fixture["id"])
            recompute_difference_fixture(fixture)
        return (f"Independently hand-derived and tolerance-bound all {len(fixtures)} integer oracles; "
                "checker recomputed them as an O(total fixture samples) consistency check.")

    record("SPEC-FIXTURE-001", fixture_check)

    record("SPEC-PHASE-CONTRACT-001", lambda: validate_p6_contract_and_fixtures(
        documents[P6_CONTRACT_PATH], documents[P6_FIXTURE_PATH], documents[PROPOSAL_PROFILE_PATH]))
    record("SPEC-QUALITY-001", lambda: p7_contract_check(documents))

    def catalog_check() -> str:
        return check_catalog(
            documents[CATALOG_PATH],
            TRACEABILITY_PATH.read_text(encoding="utf-8"),
            (SPEC_ROOT / "contracts" / "RUNTIME_INVARIANTS.md").read_text(encoding="utf-8"),
        )

    record("SPEC-CATALOG-001", catalog_check)
    record("SPEC-ADMISSION-001", lambda: p4_evidence_check(documents))
    record("SPEC-CANONICAL-001", p5_evidence_check)
    record("SPEC-SPATIAL-001", lambda: p6_evidence_check(documents))
    record("SPEC-P7-EVIDENCE-001", lambda: p7_evidence_check(documents))
    record("SPEC-P8-CONTRACT-001", lambda: p8_contract_check(documents))
    record("SPEC-P8-EVIDENCE-001", lambda: p8_evidence_check(documents))
    record("SPEC-SCOPE-001", image_scope_check)
    record("SPEC-LINKS-001", check_markdown_links)
    def policy_check() -> str:
        check_policy(documents[PROFILE_PATH])
        check_policy(documents[PROPOSAL_PROFILE_PATH])
        return "Fixture and candidate profiles retain C++/Assembly, audited-math, no-ML, and no-quadratic policies."

    record("SPEC-POLICY-001", policy_check)

    audit: dict[str, Any] = {}

    def audit_check() -> str:
        nonlocal audit
        audit, note, findings = dependency_audit()
        if findings:
            raise CheckError("dependency scope check found issues: " + "; ".join(findings[:8]))
        return note

    record("SPEC-DEPENDENCY-001", audit_check)

    run_id = "spec-check-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw_path = output_dir / "latest.raw.json"
    audit_path = output_dir / "latest.dependency_audit.json"
    evidence_path = output_dir / "latest.run_evidence.json"
    audit.setdefault("audit_scope", "Audit not completed; see failed SPEC-DEPENDENCY-001 result.")
    audit["run_id"] = run_id
    audit["generated_at"] = iso_utc()
    audit_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    results.append({"case_id": "SPEC-EVIDENCE-001", "status": "pass", "note": "Run evidence validates against its declared schema."})
    evidence_schema = documents.get(HARNESS_ROOT / "run_evidence.schema.json", {})

    def build_evidence() -> dict[str, Any]:
        schemas = {
            path.stem.replace(".schema", ""): documents[path].get("$id", "unknown")
            for path in SCHEMA_PATHS
        }
        inventory_content = {key: value for key, value in audit.items() if key not in {"run_id", "generated_at"}}
        inventory_hash = sha256_bytes(canonical_json(inventory_content).encode("utf-8"))
        all_passed = all(item["status"] == "pass" for item in results)
        catalog = documents.get(CATALOG_PATH, {})
        component_cases = catalog.get("cases", [])
        return {
            "run_id": run_id,
            "status": "finished",
            "commit": git_commit(),
            "working_tree": {
                "state": worktree_info["state"],
                "status_porcelain_sha256": worktree_info["status_porcelain_sha256"],
            },
            "profile_id": documents.get(PROPOSAL_PROFILE_PATH, {}).get("profile_id", "general-still-image-candidate-v1"),
            "profile_status": documents.get(PROPOSAL_PROFILE_PATH, {}).get("status", "proposal"),
            "profile_usage": "reference_only_no_component_execution",
            "profile_hash": sha256_file(PROPOSAL_PROFILE_PATH),
            "schema_versions": schemas,
            "input_hashes": input_hashes,
            "build": {
                "subject": "specification_harness",
                "language_boundary": "python_stdlib_only",
                "compiler_id": "not_applicable_spec_checker",
                "build_configuration": "python3 -I; standard library only; Image VISION implementation not built",
                "dependency_inventory_hash": inventory_hash,
            },
            "target": {
                "host_id": platform.platform()[:128] or "unknown-host",
                "architecture_id": platform.machine()[:128] or "unknown-architecture",
                "runtime_id": ("Python " + platform.python_version())[:128],
            },
            "seed": None,
            "reproducibility": {
                "mode": "deterministic",
                "network_access_required": False,
                "external_services_used": False,
                "nondeterministic_inputs": [],
            },
            "command": shlex.join([Path(sys.executable).name, "-I", *sys.argv]),
            "started_at": started_at,
            "finished_at": iso_utc(),
            "case_results": results,
            "counts": counts_for(results),
            "case_catalog_summary": {
                "component_cases_defined": len(component_cases),
                "component_cases_not_run": sum(case.get("execution_status") == "not_run" for case in component_cases),
                "component_cases_blocked": sum(case.get("execution_status") == "blocked" for case in component_cases),
                "component_cases_executed": 0,
                "package_checks_defined": len(catalog.get("package_checks", [])),
            },
            "resource_counters": {
                "scope": "package_checker_process_only",
                "elapsed_ms": round((time.perf_counter() - start_clock) * 1000, 3),
                "peak_rss_bytes": peak_rss_bytes(),
            },
            "dependency_audit": {
                "harness_dependency_closure_audited": audit.get("harness_dependency_closure_audited", False),
                "harness_external_dependencies_found": audit.get("harness_external_dependencies_found", False),
                "ml_libraries_frameworks_found": audit.get("ml_libraries_frameworks_found", False),
                "image_runtime_dependency_graph_audited": audit.get("image_runtime_dependency_graph_audited", False),
                "binary_audited": audit.get("binary_audited", False),
                "audit_artifact_ref": relative_ref(audit_path),
            },
            "raw_artifact_ref": relative_ref(raw_path),
        "reviewer": "user/project owner + assistant; P7 slice complete; await user approval for P8; production approval open",
            "gate_decision": "informational" if all_passed else "rejected",
        }

    evidence = build_evidence()
    evidence_errors = SubsetSchemaValidator(evidence_schema).validate(evidence, evidence_schema)
    evidence_result = results[-1]
    if evidence_errors:
        evidence_result["status"] = "fail"
        evidence_result["note"] = ("Run evidence schema validation failed: " + "; ".join(evidence_errors[:6]))[:512]
        evidence_result["output_digest"] = case_result_digest(evidence_result)
        evidence = build_evidence()
        # Preserve a usable diagnostic artifact even if the schema itself is broken.
    else:
        evidence_result["output_digest"] = case_result_digest(evidence_result)
        evidence = build_evidence()

    raw = {
        "run_id": run_id,
        "scope": "This Python run validated Image/SPEC artifacts and recorded P4/P5/P6/P7/P8 evidence; it executed no C++ component tests. Phase-specific C++ outcomes are preserved in their separate run artifacts.",
        "review_model": "user_project_owner_plus_assistant_only; no external reviewer",
        "assistant_reviewed": True,
        "project_owner_accepted": False,
        "phase_gate_decision": "p8_bounded_single_flight_engineering_slice_verified_named_workload_and_production_gate_open_phase9_unapproved",
        "commit": git_commit(),
        "working_tree_state_at_run": worktree_info["state"],
        "working_tree_status_porcelain_sha256": worktree_info["status_porcelain_sha256"],
        "started_at": started_at,
        "finished_at": iso_utc(),
        "elapsed_ms": round((time.perf_counter() - start_clock) * 1000, 3),
        "input_sha256": input_hashes,
        "catalog_summary": {
            "defined_total": len(documents.get(CATALOG_PATH, {}).get("cases", [])),
            "execution_statuses": {
                status: sum(case.get("execution_status") == status for case in documents.get(CATALOG_PATH, {}).get("cases", []))
                for status in ("not_run", "blocked")
            },
            "package_checks_defined": len(documents.get(CATALOG_PATH, {}).get("package_checks", [])),
            "component_cases_executed": 0,
        },
        "checks": results,
        "claims": {
            "Image_VISION_components_executed": False,
            "harness_dependency_closure_audited": audit.get("harness_dependency_closure_audited", False),
            "image_runtime_dependency_graph_audited": False,
            "production_binaries_audited": False,
            "semantic_or_AGI_capability_established": False,
        },
    }
    raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    passed = sum(item["status"] == "pass" for item in results)
    failed = sum(item["status"] == "fail" for item in results)
    print(f"Image/SPEC check: {passed} passed, {failed} failed; {len(results)} checker checks executed.")
    catalog_total = len(documents.get(CATALOG_PATH, {}).get("cases", []))
    catalog = documents.get(CATALOG_PATH, {})
    not_run = sum(case.get("execution_status") == "not_run" for case in catalog.get("cases", []))
    blocked = sum(case.get("execution_status") == "blocked" for case in catalog.get("cases", []))
    print(f"Catalog: {catalog_total} Image component case definitions; {not_run} not_run, {blocked} blocked in catalog lifecycle metadata; executed outcomes are stored in run artifacts.")
    print(f"Evidence: {relative_ref(evidence_path)}")
    print(f"Raw run:  {relative_ref(raw_path)}")
    print(f"Audit:    {relative_ref(audit_path)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
