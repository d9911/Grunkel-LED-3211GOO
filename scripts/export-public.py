#!/usr/bin/env python3
# Copyright (C) 2026 Denis Gutsuliak (d9911.org)
# SPDX-License-Identifier: GPL-3.0-or-later
# License and warranty notice: see LICENSE and NOTICE in the project root.
"""Export only reviewed public files; never copy the whole local working directory."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent
# Reviewed pixels only: adding a path or replacing an image requires visual review.
REVIEWED_IMAGES = {
    'assets/screenshots/couchy-satin-es.png':
        '5d13ee059014fe8a98a06f32a72736a4dd4b689be15ccbd0238b7141f960327b',
    'assets/screenshots/home-es.png':
        '3689ff99021ed432c573073329cbfdc80247c180e1976b938d906675eb88843c',
    'img/satin-teal-copper.jpg':
        '7283ecf779399fd4b174ee0fd3af06addb366b7ee0dec419ba6f1433ce5576a3',
}

PUBLIC = [
    'README.md', 'README.ru.md', 'README.es.md', 'AGENTS.md', '.gitignore',
    'package.json', 'LICENSE', 'NOTICE', 'Makefile',
    'CONTRIBUTING.md', 'CHANGELOG.md', 'docs/technical-reference.md',
    'scripts/check-project.py',
    'apps.lock.json', 'device.example.json', 'verification.json', 'hardware.json',
    'profiles/martin-mt5867-android14.json',
    'scripts/grunkel.py', 'scripts/bootstrap-adb.py', 'scripts/export-public.py',
    'scripts/generate-test-media.py', 'scripts/build-photos.py',
    'android/photos/AndroidManifest.xml',
    'android/photos/assets/locales/en.json',
    'android/photos/assets/locales/es.json',
    'android/photos/assets/locales/ru.json',
    'android/photos/src/org/d9911/grunkel/photos/MainActivity.java',
    'android/photos/src/org/d9911/grunkel/photos/PhotoData.java',
    'android/photos/src/org/d9911/grunkel/photos/PhotoDreamService.java',
    'android/photos/src/org/d9911/grunkel/photos/PhotoPreviewActivity.java',
    'android/photos/src/org/d9911/grunkel/photos/PhotoShow.java',
    'android/photos/src/org/d9911/grunkel/photos/StatusReceiver.java',
    'android/photos/toolchain.lock.json',
    'android/shortcuts/inputs/AndroidManifest.xml',
    'android/shortcuts/inputs/res/drawable/banner.xml',
    'android/shortcuts/inputs/res/values-es/strings.xml',
    'android/shortcuts/inputs/res/values-ru/strings.xml',
    'android/shortcuts/inputs/res/values/strings.xml',
    'android/shortcuts/src/org/d9911/grunkel/shortcuts/MainActivity.java',
    'android/shortcuts/usb/AndroidManifest.xml',
    'android/shortcuts/usb/res/drawable/banner.xml',
    'android/shortcuts/usb/res/values-es/strings.xml',
    'android/shortcuts/usb/res/values-ru/strings.xml',
    'android/shortcuts/usb/res/values/strings.xml',
    'scripts/build-shortcuts.py',
    'assets/showcase.json',
    'scripts/remote.py', 'remote.example.json', 'remote-tools.lock.json',
    *REVIEWED_IMAGES,
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ROOT / 'exports/Grunkel-LED-3211GOO.zip'))
    args = parser.parse_args()
    output = Path(args.output).resolve()
    contents = {}
    # Explicit opt-in whitelist. A newly added local file is never exported automatically.
    for relative in PUBLIC:
        path = ROOT / relative
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise SystemExit('Refusing a symlink or path outside the project: ' + relative)
        data = path.read_bytes()
        if relative in REVIEWED_IMAGES:
            if hashlib.sha256(data).hexdigest() != REVIEWED_IMAGES[relative]:
                raise SystemExit('Unreviewed image bytes in ' + relative)
            if relative.endswith('.png'):
                valid = data.startswith(b'\x89PNG\r\n\x1a\n')
            else:
                valid = data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9')
            if not valid:
                raise SystemExit('Invalid reviewed image format: ' + relative)
            contents[relative] = data
            continue
        text = data.decode('utf-8')
        patterns = [r'/' + r'Users/[^/\s]+/', r'\b192\.168\.\d+\.\d+\b', r'\b10\.\d+\.\d+\.\d+\b',
                    r'\b172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+\b', r'(?i)\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b',
                    r'-----BEGIN [A-Z ]*PRIVATE KEY-----']
        if any(re.search(pattern, text) for pattern in patterns):
            raise SystemExit('Possible private data in ' + relative + '; review before export.')
        contents[relative] = data
    if output in [(ROOT / name).resolve() for name in PUBLIC] or output.exists():
        raise SystemExit('Output already exists or overlaps source; choose a new --output filename.')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in contents.items():
            archive.writestr('Grunkel-LED-3211GOO/' + name, data)
    print(json.dumps({'archive': str(output), 'files': list(contents), 'published': False}, indent=2))


if __name__ == '__main__':
    main()
