# Security policy

Do not attach private signing material, keyboxes, eSIM activation data,
subscriber identifiers, device serials, ADB/Tailscale credentials, or full
device logs to an issue.

Report vulnerabilities through GitHub private vulnerability reporting when it
is enabled. Include the affected commit, a redacted reproducer, impact, and the
smallest evidence needed to validate the report.

Public install artifacts ship only through the project release channel and
carry their own SHA256SUMS and validation evidence. This ROM does not support
bootloader relocking: the owner-signed images will not verify under the
factory key set and relocking bricks the device.
