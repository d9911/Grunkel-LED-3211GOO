# Contributing and first publication

Read AGENTS.md, a user README, hardware.json and verification.json. This is a configuration toolkit for one exact build; it is not a custom ROM. Toolkit version 1.0.0 is separate from original app versions Photos 0.2.0 and Shortcuts 0.1.0.

## Before changing code

- Inspect git status/diff and preserve owner work, the existing index, USB files and private keys.
- Read scripts/grunkel.py entry points before introducing another ADB helper. Mutation must follow the exact device guard and record an original-value journal where applicable.
- Avoid generic debloat lists; protect Cast/DRM/WebView/TV services and updates. No root/reset/uninstall/data clear/partition writes for routine fixes.
- Record actual observed outcomes separately from source inspection and owner reports. No universal compatibility, zero telemetry or permanent speed claims.

## Offline verification

```sh
make check
make launcher-list
```

check reads only reviewed source files, parses Python/JSON/XML, validates README links/anchors and shared locale keys, verifies image hashes and creates/validates a temporary public ZIP outside the repository. It contacts no TV or network and downloads nothing. It is a maintenance validator, not a substitute for live app/playback checks.

For a CLI/Make behavior change, exercise the affected path with isolated fixtures or a separately authorized device; never use the owner's TV as an automatic test target. Do not create tests in main for an already covered flow. Original Java changes need the corresponding local build, signature/package/permission/hash checks, then an authorized runtime check. Keep generated APKs/signing keys private. Document untested behavior explicitly.

## Updating third-party pins

1. Use the official release/source from apps.lock.json. Review new permissions, supported Android version/ABIs and signing identity.
2. Verify the downloaded asset against the official digest; update the exact version/code/URL/hash together.
3. Do not call a source/catalog inspection a live test. Check the APK on the exact target before replacing a tested baseline.
4. Keep all three README language/version/download tables consistent. Update verification.json and CHANGELOG.md only with actual evidence.

## Images and public material

Only current Couchy HOME, the owner's preserved historical home-es.png and the original JPEG belong to the public set. Do not re-export redundant captures. Before replacing pixels, review the entire image for private content and update both assets/showcase.json and export-public.py SHA-256. These two PNGs have no pixel edits. Old removed public captures are retained privately in the pre-cleanup reserve; raw diagnostics/owner photos remain ignored.

Export explicitly, never zip the whole working directory:

```sh
make export OUTPUT=exports/Grunkel-LED-3211GOO-1.0.0.zip
```

The exporter refuses existing output files, unreviewed image bytes, escaping paths and suspicious private data. It never publishes. Native Couchy JSON can reveal package inventory. Do not commit local configs, device addresses, ADB/signing keys, APKs or backups. package.json private=true prevents accidental npm publication; it does not override the GPL grant for original source material.

## Owner's manual Git step

Agents must not stage, commit, create branches/tags or mutate any remote. The owner performs Git actions manually. A previously staged index may still contain files removed from the working tree: review/update that index before creating the initial commit. There is no configured repository URL in this copy; add repository/homepage/bugs metadata only after the owner supplies the actual URL.

Suggested single initial commit title:

```text
feat: add Grunkel LED-3211GOO setup with USB photos and three launchers
```

Suggested body: reversible ADB setup and SHA-256 pins; EN/ES/RU guides; Couchy/Projectivy/Plume initialization; original USB screensaver and HDMI/USB cards; compatibility guard, recovery journals, compact evidence and privacy-reviewed export. No commit, tag, PR, release or push is created by these scripts.
