# Release gates

This repository is ready for source review, not for installation.

Before a public ROM release:

1. Resolve the remaining vendor/external kernel-module pins and reproduce the
   documented GKI/Motorola source set, or close lawful prebuilt redistribution.
2. Qualify clean installation and runtime behavior for both embedded stock
   contracts; extraction alone does not prove device acceptance.
3. Rebase the framework to a current Android Security Bulletin level; do not
   advertise the RC1's `2026-06-01` framework SPL as current.
4. Produce a production `user` build and verify Android, APK/RRO, OTA, and AVB
   signers independently.
5. Extract every rebuilt partition and reject `test-keys`, patch rollback, and
   unplanned fingerprints before installation.
6. Qualify clean install, failed-update recovery, rollback, and data retention
   on the spare XT2303-2.
7. Re-run hardware, carrier, USB, Qi/accessory, DT2W, and signed-build
   Tailscadble acceptance.
8. Publish checksums, public trust anchors, exact install/rollback instructions,
   notices, and supported firmware contracts together.

The source gate now requires the complete 27-file stock IMS closure and binds
its manifest hash into the production stamp. It also requires the two
upstream-signed app clients and binds their manifest hash. This closes
host-input reproducibility only; it does not satisfy signed-build or
device-runtime gates.

Bootloader relocking remains unsupported until a separately tested custom-AVB
enrollment path exists.
