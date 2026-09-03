# Provenance boundary

- AOSP and LineageOS build interfaces: Apache-2.0.
- Device integration and OSverflow overlays: independently authored,
  Apache-2.0.
- The Motorola/MediaTek IMS compatibility closure is represented only by
  source paths, sizes, hashes, and local Soong imports. Its 27 proprietary
  payloads must be extracted locally and are not redistributed here.
- Hardware values and interface names: interoperability facts observed from
  the exact `V1TLS35.73-60-3-10` and `V1TLS35.73-60-3-14` stock packages and
  accepted-device behavior.
- Public GKI and Motorola kernel-source references are pinned in
  [`kernel-source-reference.json`](../kernel-source-reference.json) and
  explained in [`KERNEL_SOURCE.md`](KERNEL_SOURCE.md).

The public GKI tag maps to the accepted live release identity, and Motorola's
matching release branch contains Lyriq/MT6893 DTS and hardware drivers. The
vendor-module revision and every external-module input are not yet resolved,
so a reproducible source build is still unproven and not consumed by this tree.
The current kernel remains a hash-pinned local prebuilt.

No decoded DTS, proprietary binary, stock VINTF matrix, compiled stock SELinux
policy, or generated ABI payload is copied here.
