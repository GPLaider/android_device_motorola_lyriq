# Local input contract

From Linux or WSL, extract the exact locally obtained Software Fix directory:

```text
python tools/extract_stock.py \
  /path/to/LYRIQ_G_V1TLS35.73_60_3_10_..._CFC.xml \
  .local-prebuilts \
  --simg2img /path/to/simg2img \
  --lpunpack /path/to/lpunpack \
  --debugfs /path/to/debugfs
```

The extractor accepts only the model and build in
[`prebuilts/manifest.json`](../prebuilts/manifest.json), verifies Motorola's
MD5 for every consumed input, reconstructs `super`, extracts only the three
required logical partitions, derives `fstab.mt6893` from verified `vendor_a`,
and then checks final size and SHA-256.

Generate the build gate stamp separately:

```text
python verify_source.py --prebuilts .local-prebuilts --stamp lyriq-gate.stamp.mk
```

The verifier rechecks byte length and SHA-256 before generating the make stamp.
Neither tool downloads firmware, signs output, flashes a device, or accepts a
same-name substitute.

The recorded files came from the separately obtained Motorola Software Fix
package for `V1TLS35.73-60-3-10` / `40dcc-72d036`. This repository neither
contains those payloads nor grants redistribution permission.

Place the release AVB key at `.local-signing/lyriq-avb.pem` and the OTA public
certificate at `.local-signing/releasekey.x509.pem`. Private signing material
must never be committed or logged. APK, OTA, and AVB trust domains remain
separate.
