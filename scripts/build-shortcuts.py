#!/usr/bin/env python3
# Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
"""Build offline input/USB shortcuts using the photo app's pinned local toolchain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import secrets
import shutil
import subprocess
import sys
import uuid
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'android/shortcuts'


def build(toolchain, bootstrap=False):
    helper = runpy.run_path(str(ROOT / 'scripts/build-photos.py'))
    if bootstrap:
        helper['bootstrap']()
    config = json.loads((ROOT / 'android/photos/toolchain.lock.json').read_text())
    java = toolchain / config['java_home']
    sdk = toolchain / config['platform_jar']
    tools = toolchain / config['build_tools']
    env = dict(os.environ, JAVA_HOME=str(java))
    run = helper['run']
    out = ROOT / 'downloads' / ('shortcuts-build-' + uuid.uuid4().hex[:12])
    classes, dex = out / 'classes', out / 'dex'
    classes.mkdir(parents=True); dex.mkdir()
    run([java/'bin/javac', '--release', '8', '-encoding', 'UTF-8', '-cp', sdk, '-d', classes, *sorted((SOURCE/'src').rglob('*.java'))], env)
    run([tools/'d8', '--lib', sdk, '--min-api', '26', '--output', dex, *sorted(classes.rglob('*.class'))], env)
    signing = ROOT / 'tools/shortcut-signing'
    signing.mkdir(parents=True, exist_ok=True)
    key, password = signing/'shortcuts.jks', signing/'password.txt'
    if key.exists() != password.exists():
        raise RuntimeError('Incomplete signing material: preserve it and restore the missing file.')
    if not password.exists():
        fd = os.open(password, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(secrets.token_urlsafe(32))
    env['GRUNKEL_SHORTCUT_SIGN_PASSWORD'] = password.read_text().strip()
    if not key.exists():
        run([java/'bin/keytool', '-genkeypair', '-alias', 'grunkel-shortcuts', '-keystore', key,
             '-storepass:env', 'GRUNKEL_SHORTCUT_SIGN_PASSWORD', '-keypass:env', 'GRUNKEL_SHORTCUT_SIGN_PASSWORD',
             '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000', '-dname', 'CN=Denis Gutsuliak, O=d9911.org', '-noprompt'], env)
        key.chmod(0o600)
    artifacts = {}
    for name in ('inputs', 'usb'):
        package = 'org.d9911.grunkel.' + name
        folder = out/name; folder.mkdir()
        compiled = folder/'resources.zip'
        run([tools/'aapt2', 'compile', '--dir', SOURCE/name/'res', '-o', compiled], env)
        unsigned = folder/'unsigned.apk'
        run([tools/'aapt2', 'link', '-I', sdk, '--manifest', SOURCE/name/'AndroidManifest.xml', '-o', unsigned, compiled], env)
        with zipfile.ZipFile(unsigned, 'a', compression=zipfile.ZIP_DEFLATED) as z:
            for path in dex.glob('*.dex'):
                z.write(path, path.name)
        aligned, apk = folder/'aligned.apk', folder/('Grunkel-' + name.title() + '-0.1.0.apk')
        run([tools/'zipalign', '-p', '-f', '4', unsigned, aligned], env)
        run([tools/'apksigner', 'sign', '--ks', key, '--ks-key-alias', 'grunkel-shortcuts',
             '--ks-pass', 'env:GRUNKEL_SHORTCUT_SIGN_PASSWORD', '--key-pass', 'env:GRUNKEL_SHORTCUT_SIGN_PASSWORD', '--out', apk, aligned], env)
        cert = run([tools/'apksigner', 'verify', '--verbose', '--print-certs', apk], env)
        signer = re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)', cert)
        badging = run([tools/'aapt2', 'dump', 'badging', apk], env)
        if not signer or "package: name='" + package + "'" not in badging or 'uses-permission:' in badging:
            raise RuntimeError('Shortcut identity, permissions or signature did not match.')
        artifacts[name] = {'package': package, 'version': '0.1.0', 'apk': str(apk),
                           'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
                           'signer_sha256': signer[1], 'permissions': [], 'bytes': apk.stat().st_size}
    manifest = {'schema': 1, 'artifacts': artifacts, 'installed': False}
    pointer = ROOT/'downloads/grunkel-shortcuts-build.local.json'
    tmp = pointer.with_suffix('.tmp'); tmp.write_text(json.dumps(manifest, indent=2)+'\n'); tmp.replace(pointer)
    (out/'build.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', action='store_true')
    parser.add_argument('--toolchain', type=Path, default=ROOT/'tools/photo-android')
    args = parser.parse_args()
    build(args.toolchain.resolve(), args.bootstrap)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print('Error:', error, file=sys.stderr)
        sys.exit(1)
