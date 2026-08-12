# AGI-VS Real-World Observation Proof

**Status**: Validated observation benchmark; ready for versioned proof-package release

This proof demonstrates a specific, limited claim: the **frozen AGI Vision Substrate** accepts real-world images, converts each image into structured numerical visual signals, produces a different token signature for every reviewed image, and does so at measured speed. The benchmark contains **no training, fitting, adapter update, model checkpoint update, or C++ core modification**.

> **What this does prove:** different real-world visual inputs create different reproducible internal signal patterns.
> **What this does not prove:** semantic understanding of “city,” “animal,” “house,” or “vehicle”; video-event understanding; language alignment; or AGI-level intelligence.

![Signal-distance and latency proof](signal_distance_and_latency.png)

---

## 1. Rights-Reviewed Observation Inputs

The proof set contains eight real images retrieved from normal browser delivery paths and saved as local WebP proof copies. Every selected source has item-level **CC0 or public-domain** evidence, a source page, a delivery URL, an author/credit field when supplied, a local checksum, and a visual review. Wikimedia Commons advises reusers to verify each file’s licence and consider non-copyright restrictions; this proof therefore excludes discernible people and faces and keeps an item-level provenance record for every input [1] [2].

| Proof image | Real-world scene | Licence | Source item | Visual-review decision |
| :--- | :--- | :--- | :--- | :--- |
| `city_victoria_harbour` | Night city skyline | CC0 | [Victoria Harbour skyscrapers][4] | Pass: skyline; no discernible people/faces. |
| `city_kaohsiung` | Night city skyline and moon | CC0 | [Kaohsiung urban skyline][5] | Pass: skyline; no discernible people/faces. |
| `animal_iguana` | Iguana close-up | CC0 | [Iguana de Venezuela][6] | Pass: animal texture; no person. |
| `animal_bird` | Bird | CC0 | [Bird at Wingham Wildlife Park][7] | Pass: animal shape/colour; no person. |
| `house_quebec` | House facade | CC0 | [House facade in Quebec City][8] | Pass: house geometry; no person. |
| `building_paulista` | Building facade | CC0 | [Building in Paulista Avenue][9] | Pass: repeated architectural structure; no person. |
| `landscape_utah_dunes` | Dunes and mountains | Public domain | [Utah Dunes Landscape][10] | Pass: natural gradients and contours; no person. |
| `vehicle_place_etoile` | Vehicle close-up | CC0 | [Place de l’Étoile vehicle][11] | Pass: vehicle contours/reflections; no person. |

The fixed machine-readable source record is [`proof_set_manifest.json`](proof_set_manifest.json); the local-copy checksum and review binding is [`acquisition_manifest.json`](acquisition_manifest.json). The review log records one rejected pedestrian-prominence city candidate and one rejected building candidate with small discernible figures rather than silently retaining them.

---

## 2. What Happened to Each Image

Every local proof copy was letterboxed—not cropped—to a C-contiguous **512 × 512 RGB `float32`** input. The frozen substrate then emitted Stage 1 atomic signals, Stage 2 multi-scale/gate signals, and Stage 4 visual tokens. Each image generated **1,024 source patches**, retained **32 visual tokens**, and emitted **4,096 values per retained token**.

| Image | Energy mean | Multi-scale complexity | Token signature prefix | Median latency | p95 latency | Median FPS equivalent |
| :--- | ---: | ---: | :--- | ---: | ---: | ---: |
| Bird | 0.4063 | 0.4194 | `f929766ee718` | 10.03 ms | 10.83 ms | 99.73 |
| Iguana | 0.3564 | 0.5841 | `a075e0beea36` | 9.93 ms | 10.71 ms | 100.66 |
| Paulista building | 0.5017 | 0.6820 | `85334272eef2` | 10.00 ms | 10.39 ms | 100.03 |
| Kaohsiung city | 0.1008 | 0.2823 | `01c9f9b74836` | 9.97 ms | 10.41 ms | 100.31 |
| Victoria Harbour city | 0.1171 | 0.4794 | `6e78891147dd` | 10.13 ms | 11.98 ms | 98.67 |
| Quebec house | 0.2868 | 0.4180 | `ddfee8dd7249` | 10.05 ms | 10.77 ms | 99.47 |
| Utah dunes | 0.3644 | 0.3580 | `a254c4c0ba64` | 10.06 ms | 10.64 ms | 99.40 |
| Place de l’Étoile vehicle | 0.3742 | 0.4598 | `7c32e74495e3` | 9.92 ms | 10.27 ms | 100.85 |

The **energy mean** is a compact indicator of how the substrate measured local visual change across the normalized image. The **multi-scale complexity** is a structural measure from the wavelet-and-gate stage. The **token signature prefix** is a truncated SHA-256 digest of the full 4,096-dimensional mean-pooled Stage 4 signal; it is a reproducibility identifier, not a semantic label.

---

## 3. Signal Distinction and Integrity

The substrate produced a distinct full pooled-signal digest for every image. Across the 28 unordered image pairs, the minimum cosine distance between mean-pooled token signals was **0.029985**, the maximum was **1.015**, and the mean was recorded in the machine-readable report. A non-zero distance for every pair establishes that no two proof images collapsed to the same pooled Stage 4 signal under this fixed input contract.

Every repeated projection of the same standardized image produced a maximum absolute token difference of **0.0** within the recorded `float32` output. Input integrity reports show C-contiguous `float32` input, **no input copy**, matching input addresses in the zero-copy probe, an `AVX-512F` SIMD backend, and the `cpu-openmp-avx` accelerated path with six workers.

The complete per-image record—including Stage 1 energy/flow distribution, Stage 2 gate features and weights, Stage 4 token digest, most-important patch coordinates, determinism result, and all 30 timing samples summarized by distribution—is retained in [`signal_report.json`](signal_report.json). The complete pairwise distance values are retained in [`signal_distance_matrix.csv`](signal_distance_matrix.csv).

---

## 4. Meaning in Plain Language

The proof images do **not** turn directly into words. They turn into a different internal numerical fingerprint for each visual scene. A city skyline, an iguana’s textured body, a house facade, desert dunes, and a reflective vehicle have visibly different edges, textures, colour layouts, repeated patterns, and spatial arrangements. The substrate detects and compresses those differences into visual tokens.

Later AGI software can place a learned semantic encoder after this substrate:

```text
real image or video frame → frozen visual substrate → visual signals/tokens → semantic encoder → AGI memory, language, reasoning, and action
```

The present proof validates the left side of this chain. It does not yet establish the semantic encoder, video time/motion memory, language connection, world model, or reasoning layer.

---

## 5. Benchmark Configuration and Limits

| Item | Recorded configuration |
| :--- | :--- |
| Input workload | Each source proof copy is letterboxed to 512 × 512; no crop. |
| Measurement | Five warm-up projections plus 30 measured complete Stage 1–4 projections per image. |
| Hardware path | AVX-512F SIMD; OpenMP accelerated CPU dispatcher with six workers. |
| Token policy | 16 × 16 patches, 25% retention, maximum 32 tokens, 4,096 dimensions per token. |
| Training state | **No training and no parameter update.** |
| Scope | Eight selected real images are a functional observation proof, not a population-level real-world benchmark. |
| Video state | Individual video frames can use the same image path; temporal tracking, event representation, and video memory are not yet implemented. |

## References

[1]: https://commons.wikimedia.org/wiki/Commons:Licensing "Wikimedia Commons Licensing Policy"
[2]: https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia "Reusing Wikimedia Commons Content"
[3]: https://commons.wikimedia.org/wiki/Commons:API/MediaWiki "Wikimedia Commons Action API Examples"
[4]: https://commons.wikimedia.org/wiki/File:Victoria_Harbour_skyscrapers.jpg "Victoria Harbour Skyscrapers"
[5]: https://commons.wikimedia.org/wiki/File:Urban_skyline_of_Kaohsiung,_Taiwan_at_night.jpg "Kaohsiung Urban Skyline at Night"
[6]: https://commons.wikimedia.org/wiki/File:Iguana_de_Venezuela.jpg "Iguana de Venezuela"
[7]: https://commons.wikimedia.org/wiki/File:Bird_at_Wingham_Wildlife_Park.jpg "Bird at Wingham Wildlife Park"
[8]: https://commons.wikimedia.org/wiki/File:House_facade_in_Quebec_city,_Canada.jpg "House Facade in Quebec City"
[9]: https://commons.wikimedia.org/wiki/File:Building_in_Paulista_Avenue_09.jpg "Building in Paulista Avenue"
[10]: https://commons.wikimedia.org/wiki/File:Utah_Dunes_Landscape_-_West_Desert_District.jpg "Utah Dunes Landscape"
[11]: https://commons.wikimedia.org/wiki/File:Auto_op_de_Place_de_l%27%C3%89toile,_in_de_koplamp_is_de_weerspiegeling_van_de_Arc_de_T,_Bestanddeelnr_191-0354.jpg "Place de l’Étoile Vehicle"
