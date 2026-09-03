# OSverflow device integration for Motorola Edge 40

This repository is the source candidate for Motorola Edge 40 (`lyriq`,
XT2303-2) support in OSverflow.

It is **not an installable release**. It deliberately omits Motorola/MediaTek
payloads, signing keys, extracted stock policy, generated images, and local
evidence. The accepted OSverflow 16 RC1 remains private while clean-install,
recovery, current-ASB, production `user` build, and redistribution gates are
open.

## Two firmware contracts

- Qualified first-install baseline under review:
  `V1TLS35.73-60-3-14`.
- Hardware prebuilts used by the frozen RC1 build graph:
  `V1TLS35.73-60-3-10` / `40dcc-72d036`.

Those contracts are not interchangeable. A public installer must either
standardize all required firmware inputs or qualify every permitted baseline;
this repository currently does neither.

## Included

- Android product and dynamic-partition integration.
- Hash-pinned interface for locally supplied stock boot/vendor inputs.
- Device overlays for display, UDFPS, centered cutout, DT2W, IMS, and Lineage
  window-blur defaults.
- Lyriq-only SELinux additions and VINTF compatibility declarations.
- MGLRU/background-compaction stabilization used by the accepted RC1.
- A source verifier and a fail-closed extractor for a user-supplied Motorola
  Software Fix package.

## Excluded

- Proprietary vendor blobs and every `.img`, OTA, APK, APEX, key, and keybox.
- eSIM and AVF/Fedora experiments.
- Play Integrity, build/signature/SPL spoofing, and GmsCompat PIF overlays.
- Stock-extracted VINTF matrices and SELinux contexts.
- Boot-animation archives and rendered frames; the current adaptation's source
  asset licensing is not closed.
- Public installation, bootloader relocking, and a reproducible kernel build.

Run `python verify_source.py`. See [inputs](docs/INPUTS.md),
[provenance](docs/PROVENANCE.md), and [release gates](docs/RELEASE_GATES.md).

OSverflow is independent of Motorola, MediaTek, LineageOS, GrapheneOS, Google,
and Tailscale. Names are used only for provenance and interoperability.
