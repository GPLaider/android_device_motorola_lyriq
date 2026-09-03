# Local input contract

From Linux or WSL, extract the exact locally obtained Software Fix directory:

```text
python tools/extract_stock.py \
  /path/to/LYRIQ_G_V1TLS35.73_60_3_10_..._CFC.xml \
  .local-prebuilts \
  --contract 3-10 \
  --simg2img /path/to/simg2img \
  --lpunpack /path/to/lpunpack \
  --debugfs /path/to/debugfs \
  --fsck-erofs /path/to/fsck.erofs \
  --with-stock-ims
```

The extractor accepts only the model and build in the selected embedded
manifest: [`3-10`](../prebuilts/manifest.json) or
[`3-14`](../prebuilts/manifest-3-14.json). It verifies Motorola's MD5 for every
consumed input, reconstructs `super`, extracts only the three required logical
partitions, derives `fstab.mt6893` from verified `vendor_a`, and then checks
final size and SHA-256. `--with-stock-ims` additionally extracts the 27-file
IMS closure into `.local-prebuilts/stock-ims`; the same byte contract is valid
for both supported stock builds. Arbitrary manifests are not accepted.

Generate the build gate stamp separately:

```text
python verify_source.py --contract 3-10 --prebuilts .local-prebuilts --stamp lyriq-gate.stamp.mk
```

The verifier rechecks the seven partition inputs and all 27 IMS files before
generating the make stamp. The unused stock `OP12Ims.apk` is not part of the
build contract. Neither tool downloads firmware, signs output, flashes a
device, or accepts a same-name substitute.

The recorded contracts came from separately obtained Motorola Software Fix
packages for `V1TLS35.73-60-3-10` / `40dcc-72d036` and
`V1TLS35.73-60-3-14` / `89e5f-45c91`. This repository neither contains those
payloads nor grants redistribution permission.

For a `3-14` build, pass `--contract 3-14` to both commands and set
`LYRIQ_STOCK_CONTRACT=3-14` in the Android build environment. A stamp from one
contract is rejected by the other.

Place the release AVB key at `.local-signing/lyriq-avb.pem` and the OTA public
certificate at `.local-signing/releasekey.x509.pem`. Private signing material
must never be committed or logged. APK, OTA, and AVB trust domains remain
separate.
