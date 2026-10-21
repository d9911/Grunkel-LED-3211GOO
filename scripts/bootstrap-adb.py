#!/usr/bin/env python3
# Copyright (C) 2026 Denis Gutsuliak (d9911.org)
# SPDX-License-Identifier: GPL-3.0-or-later
# License and warranty notice: see LICENSE and NOTICE in the project root.
"""Download official Android Platform Tools locally and verify Google's archive checksum."""
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://dl.google.com/android/repository/"


def get(url):
    with urlopen(Request(url, headers={"User-Agent": "Grunkel-LED-3211GOO-setup"}), timeout=60) as stream:
        return stream.read()


def main():
    host = {"Darwin": "macosx", "Linux": "linux", "Windows": "windows"}.get(platform.system())
    if host is None:
        raise SystemExit("Unsupported host OS. Install Android SDK Platform Tools manually.")
    binary = ROOT / "tools/platform-tools" / ("adb.exe" if host == "windows" else "adb")
    if binary.is_file():
        subprocess.run([str(binary), "version"], check=True)
        return
    tree = ET.fromstring(get(BASE + "repository2-1.xml"))
    package = next(p for p in tree if p.tag.endswith("remotePackage") and p.attrib.get("path") == "platform-tools")
    archive = next(a for a in package.findall("./archives/archive") if a.findtext("host-os") == host)
    complete = archive.find("complete")
    checksum = complete.find("checksum")
    algorithm = checksum.attrib.get("type", "sha1")
    expected = checksum.text.strip()
    name = complete.findtext("url")
    if algorithm not in ("sha1", "sha256") or not name.startswith("platform-tools_") or "/" in name:
        raise SystemExit("Unexpected SDK metadata; no archive extracted.")
    data = get(BASE + name)
    if hashlib.new(algorithm, data).hexdigest() != expected:
        raise SystemExit("Google SDK archive checksum mismatch; no archive extracted.")
    downloads = ROOT / "downloads"
    downloads.mkdir(exist_ok=True)
    archive_path = downloads / name
    archive_path.write_bytes(data)
    destination = ROOT / "tools"
    destination.mkdir(exist_ok=True)
    with ZipFile(archive_path) as zipped:
        for entry in zipped.infolist():
            target = (destination / entry.filename).resolve()
            if not target.is_relative_to(destination.resolve()) or not entry.filename.startswith("platform-tools/"):
                raise SystemExit("Unsafe archive member; extraction stopped.")
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise SystemExit("Archive symlinks are not accepted.")
        zipped.extractall(destination)
        if host != "windows":
            for entry in zipped.infolist():
                permissions = (entry.external_attr >> 16) & 0o777
                if permissions and not entry.is_dir():
                    (destination / entry.filename).chmod(permissions)
    metadata = {"source": BASE + "repository2-1.xml", "url": BASE + name,
                "checksum_algorithm": algorithm, "checksum": expected,
                "sha256": hashlib.sha256(data).hexdigest()}
    (downloads / "platform-tools-source.json").write_text(json.dumps(metadata, indent=2) + "\n")
    subprocess.run([str(binary), "version"], check=True)


if __name__ == "__main__":
    main()
