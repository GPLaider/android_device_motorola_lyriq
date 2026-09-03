# Provenance boundary

- AOSP and LineageOS build interfaces: Apache-2.0.
- Device integration and OSverflow overlays: independently authored,
  Apache-2.0.
- Hardware values and interface names: interoperability facts observed from
  the `V1TLS35.73-60-3-10` stock package and accepted-device behavior.
- Exact public Motorola kernel reference:
  `MotorolaMobilityLLC/kernel-mtk`, branch
  `android-15-release-v1tl35.73-60-3`, commit
  `945dea4ed4b43c260eb9fb6135115bccd62bd80d`.

That public kernel reference does not reproduce the accepted live kernel
`6.6.89-android15-8-gdcee9aa4fcbc-ab14676413-4k`, lacks Lyriq/MT6893 board DTS,
and is not consumed by this tree. The exact kernel remains a hash-pinned local
prebuilt until lawful, reproducible source closure exists.

No decoded DTS, proprietary binary, stock VINTF matrix, compiled stock SELinux
policy, or generated ABI payload is copied here.
