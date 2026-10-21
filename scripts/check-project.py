#!/usr/bin/env python3
# Copyright (C) 2026 Denis Gutsuliak. SPDX-License-Identifier: GPL-3.0-or-later
"""Validate reviewed project material offline; never contact/configure a TV or network."""
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    export = runpy.run_path(str(ROOT / 'scripts/export-public.py'))
    public, images = export['PUBLIC'], export['REVIEWED_IMAGES']
    require(len(public) == len(set(public)), 'Duplicate public path.')
    for relative in public:
        path = ROOT / relative
        require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT), 'Missing/escaping public path: ' + relative)
        if path.suffix == '.py':
            ast.parse(path.read_text(), filename=relative)
        elif path.suffix == '.json':
            json.loads(path.read_text())
        elif path.suffix == '.xml':
            ET.parse(path)
    showcase = json.loads((ROOT / 'assets/showcase.json').read_text())
    require(showcase['sha256'] == images, 'Showcase/export image hashes disagree.')
    require(set(images) == {'assets/screenshots/home-es.png', 'assets/screenshots/couchy-satin-es.png', 'img/satin-teal-copper.jpg'}, 'Unexpected public image set.')
    for relative, digest in images.items():
        require(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, 'Unreviewed pixels: ' + relative)
    require({str(p.relative_to(ROOT)) for p in (ROOT / 'assets/screenshots').iterdir() if p.is_file()} == {p for p in images if p.endswith('.png')}, 'Redundant/unreviewed public screenshot.')
    anchors = []
    for relative in ('README.md', 'README.ru.md', 'README.es.md', 'AGENTS.md', 'CONTRIBUTING.md', 'CHANGELOG.md', 'docs/technical-reference.md'):
        text = (ROOT / relative).read_text()
        require(sum(line.lstrip().startswith('```') for line in text.splitlines()) % 2 == 0, 'Unclosed code fence: ' + relative)
        for match in re.finditer(r'!?\[[^\]]*\]\(([^\s)]+)\)', text):
            target = match[1].strip('<>')
            if target.startswith(('https:', 'http:', 'mailto:', '#')):
                continue
            filepart = target.split('#', 1)[0]
            require((ROOT / relative).parent.joinpath(filepart).is_file(), 'Broken local link: ' + relative + ' -> ' + target)
        if relative.startswith('README'):
            current = re.findall(r'<a id="([^"]+)"></a>', text)
            require(len(current) == 13, 'Expected 13 guide anchors: ' + relative)
            anchors.append(current)
            for name in ('couchy', 'projectivy', 'plume'):
                for action in ('install', 'menu', 'configure'):
                    require('make ' + action + ' TV=TV_ADDRESS:5555 LAUNCHER=' + name in text, 'Missing initialization example: ' + relative + ' ' + name + '/' + action)
    require(anchors[0] == anchors[1] == anchors[2], 'Guide anchors differ.')
    app_lock = json.loads((ROOT / 'apps.lock.json').read_text())
    for name, app in app_lock['apps'].items():
        require(re.fullmatch('[0-9a-f]{64}', app['sha256']) and app['url'].startswith('https://'), 'Invalid APK pin: ' + name)
        for guide in ('README.md', 'README.ru.md', 'README.es.md'):
            if name in ('couchy', 'projectivy', 'plume'):
                require(app['url'] in (ROOT / guide).read_text(), 'Missing official APK link: ' + guide + '/' + name)
    profile = json.loads((ROOT / 'profiles/martin-mt5867-android14.json').read_text())
    require(not (set(profile['protected_packages']) & set(profile['disable_packages'])), 'Protected package would be disabled.')
    require(profile['home_launcher'] == 'couchy', 'Unexpected default launcher.')
    catalog_paths = [ROOT / 'android/photos/assets/locales']
    for directory in catalog_paths:
        keys = [set(json.loads((directory / (lang + '.json')).read_text())) for lang in ('en', 'es', 'ru')]
        require(keys[0] == keys[1] == keys[2], 'Photo locale keys differ.')
    for name in ('inputs', 'usb'):
        base = ROOT / 'android/shortcuts' / name
        require(not ET.parse(base / 'AndroidManifest.xml').getroot().findall('uses-permission'), 'Shortcut unexpectedly requests permissions: ' + name)
        keys = [{n.attrib['name'] for n in ET.parse(path).getroot()} for path in sorted(base.glob('res/values*/strings.xml'))]
        require(len(keys) == 3 and keys[0] == keys[1] == keys[2], 'Shortcut locale keys differ: ' + name)
    require(json.loads((ROOT / 'package.json').read_text())['version'] == json.loads((ROOT / 'verification.json').read_text())['toolkit_version'], 'Toolkit versions differ.')
    # Reuse the authoritative privacy/path/image checks; only a temporary ZIP is written.
    with tempfile.TemporaryDirectory(prefix='grunkel-check-') as directory:
        output = Path(directory) / 'reviewed.zip'
        old_argv = sys.argv
        try:
            sys.argv = ['export-public.py', '--output', str(output)]
            with contextlib.redirect_stdout(io.StringIO()):
                export['main']()
        finally:
            sys.argv = old_argv
        with zipfile.ZipFile(output) as archive:
            require(archive.testzip() is None, 'ZIP CRC failed.')
            require(set(archive.namelist()) == {'Grunkel-LED-3211GOO/' + path for path in public}, 'ZIP whitelist differs.')
            for relative in public:
                require(archive.read('Grunkel-LED-3211GOO/' + relative) == (ROOT / relative).read_bytes(), 'ZIP bytes differ: ' + relative)
    print(json.dumps({'ok': True, 'offline': True, 'tv_contacted': False, 'network_used': False,
                      'public_files': len(public), 'reviewed_images': len(images),
                      'checks': ['Python/JSON/XML', 'three guide links/anchors/init variants', 'APK pins', 'locale keys', 'profile invariants', 'image hashes', 'privacy-whitelist ZIP CRC/byte parity']}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, SyntaxError, ET.ParseError) as error:
        print('Check failed:', error, file=sys.stderr)
        sys.exit(1)
