# Real-World Observation Proof Error Cycles

| Cycle | Observed condition | Containment and correction | Final effect |
| :---: | :--- | :--- | :--- |
| 1 | Scripted download requests to all eight approved Wikimedia delivery URLs returned `HTTP 429 Too Many Requests`. | No retry loop, proxy, mirror, or access-control bypass was used. The failed acquisition recorded zero retained images. The reviewed normal browser delivery path was used for one bounded local proof copy per source. | Eight local copies were saved only after their exact item-level source record and licence evidence were frozen. |
| 2 | The initially reviewed Hung Hom city panorama contained discernible pedestrians. | The candidate was rejected before retention and replaced by the CC0 Victoria Harbour skyline. | The final city proof images contain no discernible people or faces. |
| 3 | The initially selected Oslo Opera House image contained small discernible human figures. | The candidate was rejected before retention and replaced by a CC0 Quebec house facade. | The final building/house proof images remain within the declared no-people boundary. |
| 4 | The first final package validation found Markdown trailing whitespace in three proof-document lines. | Formatting was normalized and all structured-artifact checks were rerun. | The package is clean for version control; no evidence content changed. |

These cycles did not change the AGI-VS core, parameters, or outputs. The final proof benchmark is a frozen observation run with no model training.
