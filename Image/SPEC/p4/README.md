# Phase 4: decoded-raster admission and bounded P5/P6 decode

**Status at P4 closeout:** The D-015 Phase 4 engineering scope was implemented and verified; project-owner review was pending before Phase 5. The user later approved the bounded P5 transition under D-016; the identity-only P5 result is recorded in [`../P5_CLOSEOUT_RECORD.md`](../P5_CLOSEOUT_RECORD.md). The profile remains `status: proposal`, every numeric ceiling is a test candidate rather than a production limit, and no production security/release approval is claimed.

## Implemented scope

`raster_admission.hpp` and `.cpp` provide two separate entry points:

- `admit(...)` validates a caller-owned, tightly packed HWC `uint8` decoded-raster descriptor with GRAY/RGB/RGBA channel order and returns a read-only non-owning view. It performs no allocation or sample scan.
- `decode_binary_pnm(...)` accepts exactly one binary Netpbm P5 (8-bit grayscale) or P6 (8-bit RGB) image. It returns an owned raster tagged with `DecodedRaster::decoder_id` (`agi-image-pnm-p5-p6-v1`) and typed `DecodedFormat` provenance.

The decoder requires the magic bytes at offset zero, decimal positive width and height, `maxval == 255`, a bounded header, and an exact raster byte count. It accepts PNM whitespace and comments between header tokens; the required separator after `maxval` is consumed (CRLF is handled as one line ending). It rejects ASCII P2/P3, P4/P7, other max values, malformed or overflowing numbers, zero dimensions, truncated rasters, trailing data, and concatenated/multipage images. It performs no color conversion, orientation correction, alpha handling, resize, or observation assembly.

Every decoder limit is supplied by the caller through `DecodeLimits`; no production defaults are embedded. Before output allocation the implementation checks encoded size, host pointer-difference representability, header cap, positive dimensions, per-dimension and pixel ceilings, channel cap, checked pixel/sample products, decoded-byte ceiling, work ceiling, and exact input length. `work_units` is the checked sum of encoded bytes plus decoded output bytes. Failures are typed and return an empty raster (`state_changed() == false`, `retryable() == false`). Cancellation and steady-clock deadline checks run at entry, before allocation, in bounded 64-KiB copy chunks, and before success.

For input byte count `B`, pixel count `P`, and bounded channel count `C≤3`, decode time is `O(B + P*C)` and owned output storage is `O(P*C)`; parser state is `O(1)`. Header scanning is bounded by the caller's `max_header_bytes`; raster output allocation occurs only after all arithmetic and exact-size checks pass. The implementation uses only the C++ standard library and has no external decoder or codec dependency.

## Candidate profile and limits

The proposal enables only `PNM_P5` and `PNM_P6` for this engineering subset, with a candidate `max_encoded_bytes` of 67,108,864 bytes and candidate `max_work_units` of 134,217,728 (encoded bytes plus decoded bytes, or the larger feature-operation bound). Candidate width and height are 4096, pixel cap is 16,777,216, decoded-byte cap is 67,108,864, and channels are capped at four for the broader decoded-raster envelope. Test inputs also supply a 65,536-byte header ceiling as an explicit test value. **None of these values is production-approved.** The actual consumer, target, approved limits, owner appointments, deployment, and production security/release authority remain open.

## Running and checking

From the repository root:

```sh
python3 Image/SPEC/harness/p4/run_p4.py
python3 -I Image/SPEC/harness/check_spec.py
```

The P4 runner builds strict C++20 binaries in a temporary directory, runs the 33-case normal suite and AddressSanitizer/UndefinedBehaviorSanitizer suite when supported, audits standard-library includes and host dynamic links, and writes [`../harness/results/latest.p4.run_evidence.json`](../harness/results/latest.p4.run_evidence.json). The evidence binds source, header, tests, profile, commit, and working-tree state. The Python package checker separately validates specification artifacts, schema, and exact catalog bindings; it does not execute the C++ suite.

## Verified evidence and boundary

The current fresh run passes **33/33 cases in the normal build and 33/33 with ASan/UBSan**. Cases cover descriptor admission; P5/P6 sample fidelity; comments and CRLF; malformed headers, numeric overflow, unsupported variants and sample ranges; truncated, extra, and concatenated payloads; caller-supplied byte/dimension/channel/pixel/header/work ceilings; pre-allocation rejection; cancellation/deadlines; exact small bounds; and a proposal-only 4096×4096 P5 decode. The package checker additionally verifies each test-to-catalog binding.

This is an engineering/test-scope completion, not a production decoder approval or whole-package release. Formats other than P5/P6, non-255 samples, animation/multipage, metadata-based orientation/color decisions, and external codec libraries remain unsupported. The profile is not production-approved, independent external review is not claimed, and Cortex remains unchanged. At the time of the P4 closeout, Phase 5 was not yet started; it was subsequently authorized as a bounded identity-only slice under D-016. See [`../P4_CLOSEOUT_RECORD.md`](../P4_CLOSEOUT_RECORD.md), [`../P5_CLOSEOUT_RECORD.md`](../P5_CLOSEOUT_RECORD.md), and [`../DECISIONS.md`](../DECISIONS.md).
