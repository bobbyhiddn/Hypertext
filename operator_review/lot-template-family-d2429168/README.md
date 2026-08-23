# Canonical Lot template family review

This labeled matrix is composed deterministically from the checked-in 5-, 6-, and 7-card source templates. Each cell identifies its source and digest in `manifest.json`; recipes and rewards resolve through `schema/lot_template_family.json` to `templates/phases.yml`.

Review scope: `REQ-PPAUG-017` and `REQ-PPAUG-004`. No model call is part of this composition path, and scheduled generation remains disabled.

The compositor currently resolves DejaVu Serif through Pillow by font name. The repository contains no approved font binary, so pinning a new file would create an unapproved visual baseline; deterministic runs require the supported environment to provide that font.
