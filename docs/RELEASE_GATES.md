# Release gates

This repository is ready for source review, not for installation.

Before a public ROM release:

1. Close exact kernel source or explicitly lawful prebuilt redistribution.
2. Qualify the user-run stock extractor for every declared installation
   baseline; only the exact `V1TLS35.73-60-3-10` payload contract is pinned now.
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

Bootloader relocking remains unsupported until a separately tested custom-AVB
enrollment path exists.
