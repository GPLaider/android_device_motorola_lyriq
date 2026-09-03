# OSverflow device integration for Motorola Edge 40

This repository is the source candidate for Motorola Edge 40 (`lyriq`,
XT2303-2) support in OSverflow.

It is **not an installable release**. It deliberately omits Motorola/MediaTek
payloads, signing keys, extracted stock policy, generated images, and local
evidence. The accepted OSverflow 16 RC1 remains private while clean-install,
recovery, current-ASB, production `user` build, and redistribution gates are
open.

## Two firmware contracts

- Default contract and hardware prebuilts used by the frozen RC1 build graph:
  `V1TLS35.73-60-3-10` / `40dcc-72d036`.
- Second contract and qualified first-install baseline under review:
  `V1TLS35.73-60-3-14` / `89e5f-45c91`.

Those contracts are not interchangeable. Selection is explicit and binds the
hash manifest, boot fingerprint, and build stamp. Physical clean-install and
runtime qualification remain separate release gates.

## Included

- Android product and dynamic-partition integration.
- Hash-pinned interface for locally supplied stock boot/vendor inputs and the
  27-file Motorola/MediaTek IMS compatibility closure.
- Pinned public GKI/Motorola kernel-source reference with explicit unresolved
  reproducibility gaps.
- Device overlays for display, UDFPS, centered cutout, DT2W, IMS, and Lineage
  window-blur defaults.
- Lyriq-only SELinux additions and VINTF compatibility declarations.
- MGLRU/background-compaction stabilization used by the accepted RC1.
- A source verifier and a fail-closed extractor for a user-supplied Motorola
  Software Fix package; no host-specific vendor tree is required.

## Excluded

- Proprietary vendor blobs and every `.img`, OTA, APK, APEX, key, and keybox.
- eSIM and AVF/Fedora experiments.
- Play Integrity, build/signature/SPL spoofing, and GmsCompat PIF overlays.
- Stock-extracted VINTF matrices and SELinux contexts.
- Boot-animation archives and rendered frames; the current adaptation's source
  asset licensing is not closed.
- Public installation, bootloader relocking, and a reproducible kernel build.

Run `python verify_source.py`. See [inputs](docs/INPUTS.md),
[kernel sources](docs/KERNEL_SOURCE.md), [provenance](docs/PROVENANCE.md), and
[release gates](docs/RELEASE_GATES.md).

OSverflow is independent of Motorola, MediaTek, LineageOS, GrapheneOS, Google,
and Tailscale. Names are used only for provenance and interoperability.
