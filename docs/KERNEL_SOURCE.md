# Public kernel-source boundary

The exact GKI release identity is public, and Motorola publishes substantial
Lyriq hardware source. The complete source-built kernel remains unqualified
because one vendor-module revision and several external-module pins are not yet
resolved. The machine-readable pins are in
[`kernel-source-reference.json`](../kernel-source-reference.json).

## Exact GKI identity

The recorded stock kernel is:

```text
6.6.89-android15-8-gdcee9aa4fcbc-ab14676413-4k
```

Google's public
[`android15-6.6-2025-06_r38`](https://android.googlesource.com/kernel/common/+/refs/tags/android15-6.6-2025-06_r38)
tag resolves to commit `dcee9aa4fcbcdddb2cebcf0861342ad61af662f5` and
links Android CI build `14676413`. Those values match the commit prefix and
build ID embedded in the recorded release string. This is exact identity
mapping, not a byte-for-byte rebuild result.

## Motorola release sources

The exact branch `android-15-release-v1tl35.73-60-3` currently resolves to:

| Repository | Commit |
| --- | --- |
| [`kernel-mtk`](https://github.com/MotorolaMobilityLLC/kernel-mtk) | `945dea4ed4b43c260eb9fb6135115bccd62bd80d` |
| [`kernel-kernel_device_modules-6.6`](https://github.com/MotorolaMobilityLLC/kernel-kernel_device_modules-6.6) | `1a9caf9b0398f0bcb59538decfcb68d4067543bb` |
| [`motorola-kernel-modules`](https://github.com/MotorolaMobilityLLC/motorola-kernel-modules) | `d238112737a64f6d3eb47b2fce266f9c0b21c6c3` |
| [`vendor-mediatek-kernel_modules-mtkcam`](https://github.com/MotorolaMobilityLLC/vendor-mediatek-kernel_modules-mtkcam) | `226de36e40cbfc09496838491dfa7b85e1cdfd01` |
| [`vendor-mediatek-kernel_modules-gpu`](https://github.com/MotorolaMobilityLLC/vendor-mediatek-kernel_modules-gpu) | `7cdfce8d90a2ef4c6b11e7f60dcad6314445a77f` |

The device-modules tree contains `mt6893.dts`, `mt6893.dtsi`, Lyriq overlays,
Lyriq release configs, touch and camera sources. The Motorola modules tree
contains Goodix fingerprint/touch code and CPS4038 wireless-charging code. The
earlier conclusion that the public release lacked Lyriq DTS was therefore
incomplete.

## Remaining source-build gap

- Stock vendor modules identify source prefix `dd1959dca923`; that prefix did
  not resolve in the three principal public Motorola histories checked.
- The published device-module build config references eight external MTK
  repositories which exist but expose no matching `v1tl35.73-60-3` branch, plus
  an unmapped `vendor/mediatek/tests/kernel/ktf_testcase` path.
- Exact toolchain, config composition, module order, KMI, and output image hashes
  have not been reproduced from this public set.

Therefore this tree still consumes only the separately hash-pinned stock
prebuilt contract. A source-built kernel may replace it only after the missing
revisions are resolved and a clean rebuild matches the required identity and
KMI gates.
