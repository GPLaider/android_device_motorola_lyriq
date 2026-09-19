# OSverflow Edge 40 — OSVLYRIQ1

First public release of OSverflow for the Motorola Edge 40 (lyriq, MT6893 / Dimensity 8020 class), based on LineageOS 23.2 / Android 16 (BP4A.251205.006), framework security patch 2026-08-01.

Build fingerprint: `motorola/osverflow_lyriq/lyriq:16/BP4A.251205.006/OSVLYRIQ1:userdebug/release-keys`

## Highlights

- **eSIM on all SKUs.** The stock firmware ships the eUICC hardware path but omits the feature declaration on certain regional SKUs. OSverflow declares `android.hardware.telephony.euicc`, maps the non-removable eUICC slot, and bundles EuiccGoogle (LPA) plus EuiccPartnerApp with the required privileged permission grants — so eSIM profiles can be downloaded, switched, and deleted on units where stock hid the menu entirely. Verified on two physically distinct SKU units.
- **CraftedG.** A beyond-ordinary GmsCompat integration spanning 26 source repositories: custom classloader paths, hidden-API exemptions, binder/AIDL surface, selinux policy, and permission plumbing so Google services run as a trusted compatibility layer. GmsCompat is presigned with a dedicated application key that remains private.
- **Tailscadble.** Tailscale/Tailcat remote-ADB transport selection in Settings. Tailcat mode binds authenticated ADB to loopback and requires a separately running Tailcat server/forward; it does not install or autostart one. Tailscale mode retains the VPN-address-only policy. Debugging is opt-in and resets on reboot.
- **Circle to Search.** Native provider wiring with preserved HOME long-press behavior: an existing custom action is kept until the user explicitly enables Circle to Search, which then assigns the native SEARCH action. Conflicting custom actions display OFF rather than falsely reporting a working gesture. Requires the Google app with an enabled native contextual-search entrypoint (not included).
- **Rooted debugging.** `userdebug` build with `service.adb.root=1`; `adb root` yields `uid=0(root)` in `u:r:su:s0` while SELinux stays Enforcing.
- **Owner-signed everything.** All 133 rebuilt APKs and 35 signable APEXes verified against owner release certificates; AVB `vbmeta`/`vbmeta_system` chains verified against the owner AVB public key (rollback index 1785542400); OTA payload and package signatures verified.
- **Stock vendor preservation.** The package ships only OSverflow-owned images. Stock `boot`, `dtbo`, `vendor`, `vendor_boot`, `system_dlkm`, and `vendor_dlkm` from the required firmware contract remain in place and were verified byte-identical to the stock 3-14 payload.
- **Original boot animation**, Viettel CarrierConfig corrections, bundled FDroid and GrapheneOS Apps stores.

## Requirements

- Motorola Edge 40 (lyriq), unlockable-bootloader SKU
- Stock firmware **exactly `V1TLS35.73-60-3-14`** before installing — the shipped vbmeta carries hash descriptors that only verify against that build
- Unlocked bootloader. Unlocking wipes userdata and permanently downgrades Widevine to L3 (Motorola policy; no ROM can restore L1)
- **Never relock the bootloader** on this ROM — owner-signed images will not verify under the factory key set and relocking bricks the device

## Installation

See `INSTALL.md` and `scripts/osv-public-install.sh`. The installer verifies the codename, active slot, fastbootd state, stock contract, and package SHA256SUMS; resizes the logical partitions (the images exceed stock allocation); flashes `product`/`system`/`system_ext` in fastbootd, then `vbmeta`/`vbmeta_system` from LK fastboot.

- Stock → OSverflow (stock fingerprint detected): performs `fastboot -w` — userdata is wiped
- OSverflow → OSverflow (OSverflow fingerprint detected): userdata is preserved, no wipe
- Updating from builds signed by other keys is not supported

## Runtime evidence (two devices)

- Phone 1 (ZY22J58799): OSverflow→OSverflow update path, userdata and eSIM preserved, two distinct normal boots on slot B, `uid=0(root)`, `u:r:su:s0`, Enforcing; Viettel LTE IN_SERVICE (voice/SMS/video/data), carrier aggregation on, IMS APN connected; eUICC feature, controller, EuiccGoogle and EuiccPartnerApp present; Tailscale app and settings preserved
- Phone 2 (ZY22HZPLL8): same update path, one verified boot, `uid=0(root)`, `u:r:su:s0`, Enforcing

## Known limitations

- Stock → OSverflow first install (the `fastboot -w` path) has not been exercised on a third device
- Inactive-slot OTA installation and rollback are signed but not end-to-end accepted; flash the image package instead
- Complete carrier/voice/SMS coverage across all operators is not claimed; a previously observed intermittent IMS registration on one unit remains under watch
- Play Integrity and Widevine levels are not release guarantees
- No public OTA feed is enabled by this release

## Verification

`SHA256SUMS` covers every file in this package. `evidence/` contains the independent validation output: AVB verify-info for both vbmeta images, rollback indexes, signed-image hashes, OTA package signature, and the static validation RESULTS. Run `scripts/osv-public-verify.sh` after flashing to check fingerprint, slot, root, and SELinux state.

## Source

Reproducible source is published under https://github.com/OSverflow/ — device tree plus OSverflow forks of the 26 patched upstream projects, pinned in `osverflow-lyriq.xml`. Private signing keys (APK/APEX, AVB, and the GmsCompat application key) are not published; builds made from source must generate their own keys.
