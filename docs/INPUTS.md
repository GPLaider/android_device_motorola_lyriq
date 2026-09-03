# Local input contract

Put locally obtained files under `.local-prebuilts/` with the names in
[`prebuilts/manifest.json`](../prebuilts/manifest.json), then run:

```text
python verify_source.py --prebuilts .local-prebuilts --stamp lyriq-gate.stamp.mk
```

The verifier checks byte length and SHA-256 before generating the make stamp.
It never downloads firmware or accepts a same-name substitute.

The recorded files came from the separately obtained Motorola Software Fix
package for `V1TLS35.73-60-3-10` / `40dcc-72d036`. This repository neither
contains those payloads nor grants redistribution permission.

Place the release AVB key at `.local-signing/lyriq-avb.pem` and the OTA public
certificate at `.local-signing/releasekey.x509.pem`. Private signing material
must never be committed or logged. APK, OTA, and AVB trust domains remain
separate.
