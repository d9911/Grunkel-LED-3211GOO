#!/usr/bin/env python3
# Copyright (C) 2026 Denis Gutsuliak (d9911.org)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Build the offline photo app with pinned local Android tools; never install it or touch USB."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'android/photos'
TOOLS = ROOT / 'tools/photo-android'


def inside(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def bootstrap():
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise RuntimeError('Automatic tool download is pinned for macOS arm64. Use --toolchain with compatible local tools on other hosts.')
    TOOLS.mkdir(parents=True, exist_ok=True)
    for item in json.loads((SOURCE / 'toolchain.lock.json').read_text())['archives']:
        archive = TOOLS / item['filename']
        if not archive.exists():
            partial = archive.with_name(archive.name + '.partial-' + uuid.uuid4().hex[:6])
            req = urllib.request.Request(item['url'], headers={'User-Agent': 'Grunkel-photo-builder'})
            with urllib.request.urlopen(req, timeout=120) as incoming, partial.open('xb') as out:
                shutil.copyfileobj(incoming, out)
            if hashlib.sha256(partial.read_bytes()).hexdigest() != item['sha256']:
                raise RuntimeError('Tool checksum mismatch; partial archive preserved for inspection.')
            partial.rename(archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != item['sha256']:
            raise RuntimeError('Cached tool checksum mismatch: ' + item['filename'])
        target = TOOLS / item['directory']
        if target.exists():
            continue
        target.mkdir()
        if archive.name.endswith('.zip'):
            with zipfile.ZipFile(archive) as z:
                for info in z.infolist():
                    if not inside(target / info.filename, target):
                        raise RuntimeError('Unsafe tool archive path.')
                z.extractall(target)
                for info in z.infolist():
                    mode = (info.external_attr >> 16) & 0o777
                    if mode:
                        (target / info.filename).chmod(mode)
        else:
            with tarfile.open(archive) as t:
                for info in t.getmembers():
                    destination = target / info.name
                    if not inside(destination, target):
                        raise RuntimeError('Unsafe JDK archive path.')
                    if info.issym() or info.islnk():
                        link = (destination.parent if info.issym() else target) / info.linkname
                        if not inside(link, target):
                            raise RuntimeError('Unsafe JDK archive link.')
                    if not (info.isfile() or info.isdir() or info.issym() or info.islnk()):
                        raise RuntimeError('Unsupported JDK archive entry.')
                if sys.version_info >= (3, 12):
                    t.extractall(target, filter='data')
                else:
                    t.extractall(target)


def run(args, env):
    result = subprocess.run([str(x) for x in args], env=env, capture_output=True, text=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'Build command failed.')
    return result.stdout


def build(toolchain):
    config = json.loads((SOURCE / 'toolchain.lock.json').read_text())
    java = toolchain / config['java_home']
    sdk = toolchain / config['platform_jar']
    tools = toolchain / config['build_tools']
    for p in (java / 'bin/java', java / 'bin/javac', java / 'bin/keytool', sdk, tools / 'aapt2', tools / 'd8', tools / 'apksigner'):
        if not p.is_file():
            raise RuntimeError('Tool missing: ' + str(p))
    env = dict(os.environ)
    env['JAVA_HOME'] = str(java)
    out = ROOT / 'downloads' / ('photo-build-' + uuid.uuid4().hex[:12])
    classes, dex = out / 'classes', out / 'dex'
    classes.mkdir(parents=True); dex.mkdir()
    # Display data belongs in equivalent per-language JSON catalogs.
    catalogs = [json.loads((SOURCE / 'assets/locales' / (lang + '.json')).read_text()) for lang in ('en', 'es', 'ru')]
    if not all(set(c) == set(catalogs[0]) for c in catalogs):
        raise RuntimeError('Photo app language keys differ.')
    sources = sorted((SOURCE / 'src').rglob('*.java'))
    run([java / 'bin/javac', '--release', '8', '-encoding', 'UTF-8', '-cp', sdk, '-d', classes, *sources], env)
    resources = out / 'resources.apk'
    run([tools / 'aapt2', 'link', '-I', sdk, '--manifest', SOURCE / 'AndroidManifest.xml', '-A', SOURCE / 'assets', '-o', resources], env)
    run([tools / 'd8', '--lib', sdk, '--min-api', '26', '--output', dex, *sorted(classes.rglob('*.class'))], env)
    unsigned = out / 'unsigned.apk'
    shutil.copyfile(resources, unsigned)
    with zipfile.ZipFile(unsigned, 'a', compression=zipfile.ZIP_DEFLATED) as z:
        for path in dex.glob('*.dex'):
            z.write(path, path.name)
    aligned, apk = out / 'aligned.apk', out / 'Grunkel-Photos-0.2.0.apk'
    run([tools / 'zipalign', '-p', '-f', '4', unsigned, aligned], env)
    signing = ROOT / 'tools/photo-signing'
    signing.mkdir(parents=True, exist_ok=True)
    key, password = signing / 'photos.jks', signing / 'password.txt'
    if key.exists() != password.exists():
        raise RuntimeError('Incomplete signing material; preserve it and restore the missing file instead of replacing the key.')
    if not password.exists():
        fd = os.open(password, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(secrets.token_urlsafe(32))
    env['GRUNKEL_PHOTO_SIGN_PASSWORD'] = password.read_text().strip()
    if not key.exists():
        run([java / 'bin/keytool', '-genkeypair', '-alias', 'grunkel-photos', '-keystore', key,
             '-storepass:env', 'GRUNKEL_PHOTO_SIGN_PASSWORD', '-keypass:env', 'GRUNKEL_PHOTO_SIGN_PASSWORD',
             '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000', '-dname', 'CN=Denis Gutsuliak, O=d9911.org', '-noprompt'], env)
        key.chmod(0o600)
    run([tools / 'apksigner', 'sign', '--ks', key, '--ks-key-alias', 'grunkel-photos',
         '--ks-pass', 'env:GRUNKEL_PHOTO_SIGN_PASSWORD', '--key-pass', 'env:GRUNKEL_PHOTO_SIGN_PASSWORD', '--out', apk, aligned], env)
    certificate = run([tools / 'apksigner', 'verify', '--verbose', '--print-certs', apk], env)
    badging = run([tools / 'aapt2', 'dump', 'badging', apk], env)
    if "package: name='org.d9911.grunkel.photos'" not in badging or "android.permission.INTERNET" in badging:
        raise RuntimeError('Unexpected package identity or network permission.')
    signer = re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)', certificate)
    if not signer:
        raise RuntimeError('Signing certificate verification failed.')
    manifest = {'schema': 1, 'package': 'org.d9911.grunkel.photos', 'version': '0.2.0',
                'apk': str(apk), 'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
                'signer_sha256': signer[1], 'network_permission': False, 'installed': False}
    pointer = ROOT / 'downloads/grunkel-photos-build.local.json'
    temp = pointer.with_suffix('.tmp'); temp.write_text(json.dumps(manifest, indent=2) + '\n'); temp.replace(pointer)
    (out / 'build.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'apk': str(apk), 'bytes': apk.stat().st_size, 'sha256': manifest['sha256'],
                      'signature_verified': True, 'network_permission': False, 'installed': False}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bootstrap', action='store_true')
    parser.add_argument('--toolchain', type=Path, default=TOOLS)
    args = parser.parse_args()
    if args.bootstrap:
        bootstrap()
    build(args.toolchain.resolve())


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print('Error:', error, file=sys.stderr)
        sys.exit(1)
