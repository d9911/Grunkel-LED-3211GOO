#!/usr/bin/env python3
# Copyright (C) 2026 Denis Gutsuliak (d9911.org)
# SPDX-License-Identifier: GPL-3.0-or-later
# License and warranty notice: see LICENSE and NOTICE in the project root.
"""Read, configure and restore the tested Grunkel TV using official ADB."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from urllib.request import Request, urlopen
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = ROOT / "profiles/martin-mt5867-android14.json"
DEFAULT_APPS = ("couchy", "smarttube", "opentv", "airplay", "browser")
INSTALL_SOURCES = {"projectivy": "com.spocky.projengmenu", "browser": "com.phlox.tvwebbrowser", "plume": "dev.plume", "files": "me.zhanghai.android.files"}
HOME_LAUNCHERS = {"projectivy": "com.spocky.projengmenu/.ui.home.MainActivity", "plume": "dev.plume/.MainActivity", "couchy": "com.conreo.couchytv/.MainActivity"}
LAUNCHER_STATE = ROOT / "launcher.local.json"
FILES_PACKAGE = "me.zhanghai.android.files"
FILES_OP = "MANAGE_EXTERNAL_STORAGE"
SHORTCUT_PACKAGES = {name: "org.d9911.grunkel." + name for name in ("inputs", "usb")}


def configured_home(tv):
    name = tv.profile.get("home_launcher", "projectivy")
    if name not in HOME_LAUNCHERS:
        raise ValueError("Unsupported home_launcher in profile.")
    return name, HOME_LAUNCHERS[name]

INSTALL_OP = "REQUEST_INSTALL_PACKAGES"
APP_OP_MODES = {"allow", "ignore", "deny", "default", "foreground"}
PHOTO_PACKAGE = "org.d9911.grunkel.photos"
PHOTO_COMPONENT = PHOTO_PACKAGE + "/.PhotoDreamService"
PHOTO_POLICY = (("secure", "screensaver_components", PHOTO_COMPONENT),
                ("secure", "screensaver_default_component", PHOTO_COMPONENT),
                ("secure", "screensaver_enabled", "1"),
                ("secure", "screensaver_activate_on_sleep", "1"),
                ("system", "screen_off_timeout", "300000"),
                ("secure", "sleep_timeout", "1800000"))


def stamp():
    return dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S%z") + "-" + uuid.uuid4().hex[:6]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def launcher_state():
    if not LAUNCHER_STATE.exists():
        return {"format": 1, "devices": {}}
    data = json.loads(LAUNCHER_STATE.read_text())
    if not isinstance(data, dict) or data.get("format") != 1 or not isinstance(data.get("devices"), dict):
        raise ValueError("Invalid private launcher.local.json; inspect it before changing HOME.")
    for serial, entry in data["devices"].items():
        if not isinstance(serial, str) or not isinstance(entry, dict) or entry.get("name") not in HOME_LAUNCHERS or not isinstance(entry.get("fingerprint"), str):
            raise ValueError("Invalid saved launcher entry; no selection guessed.")
    return data


def device_serial(args):
    serial = args.serial or os.environ.get("GRUNKEL_TV_SERIAL")
    for name in ("device.local.json", "device.json"):
        config = ROOT / name
        if not serial and config.exists():
            serial = json.loads(config.read_text()).get("adb_address")
    if serial and not re.fullmatch(r"[A-Za-z0-9_.:\[\]%-]+", serial):
        raise ValueError("Invalid ADB serial. Use the exact value from adb devices -l.")
    return serial


def selected_configuration(args):
    profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    serial = device_serial(args)
    name = getattr(args, "launcher", None) or os.environ.get("GRUNKEL_LAUNCHER")
    if not name and serial:
        saved = launcher_state()["devices"].get(serial)
        if saved:
            if saved["fingerprint"] != profile["tested_fingerprint"]:
                raise ValueError("Saved launcher belongs to a different firmware profile; select --launcher explicitly after review.")
            name = saved["name"]
    name = name or profile.get("home_launcher", "projectivy")
    if name not in HOME_LAUNCHERS:
        raise ValueError("Choose launcher: " + ", ".join(sorted(HOME_LAUNCHERS)))
    profile["home_launcher"] = name
    packages = {component.split("/")[0] for component in HOME_LAUNCHERS.values()}
    selected = HOME_LAUNCHERS[name].split("/")[0]
    profile["required_packages"] = [p for p in profile["required_packages"] if p not in packages] + [selected]
    profile["protected_packages"] = [p for p in profile["protected_packages"] if p not in packages] + [selected]
    return serial, profile


def default_apps(tv):
    return (configured_home(tv)[0], *DEFAULT_APPS[1:])


def save_launcher_selection(tv, path, state, name):
    data = launcher_state()
    before = data["devices"].get(tv.serial)
    after = {"name": name, "fingerprint": tv.profile["tested_fingerprint"]}
    if before == after:
        return
    change = {"type": "launcher-selection", "before": before, "after": after,
              "file_existed": LAUNCHER_STATE.exists(), "status": "pending"}
    state["changes"].append(change)
    write_json(path, state)
    data["devices"][tv.serial] = after
    write_json(LAUNCHER_STATE, data)
    if launcher_state()["devices"].get(tv.serial) != after:
        raise RuntimeError("Local launcher selection was not saved; use the rollback journal.")
    change["status"] = "applied"
    write_json(path, state)


class TV:
    def __init__(self, args):
        self.serial, self.profile = selected_configuration(args)
        bundled = ROOT / "tools/platform-tools" / ("adb.exe" if os.name == "nt" else "adb")
        self.binary = os.environ.get("ADB") or (str(bundled) if bundled.exists() else shutil.which("adb"))
        if not self.binary:
            raise RuntimeError("ADB missing: install official Android Platform Tools or set ADB.")

    def adb(self, *args, timeout=60):
        result = subprocess.run([self.binary, *map(str, args)], capture_output=True, timeout=timeout)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace") or result.stdout.decode(errors="replace"))
        return result.stdout

    def require_serial(self):
        if not self.serial:
            raise RuntimeError("Select a TV with --serial, GRUNKEL_TV_SERIAL or device.local.json.")

    def shell(self, *args):
        self.require_serial()
        # adb shell joins arguments into a remote shell command. Quote each argument explicitly.
        command = " ".join(shlex.quote(str(arg)) for arg in args)
        return self.adb("-s", self.serial, "shell", command).decode(errors="replace").strip()

    def identity(self):
        keys = list(self.profile["tested_identity"]) + ["ro.build.fingerprint", "ro.boot.vbmeta.device_state"]
        return {key: self.shell("getprop", key) for key in keys}

    def guard(self):
        self.require_serial()
        if self.adb("-s", self.serial, "get-state").decode().strip() != "device":
            raise RuntimeError("The selected TV is not authorized and online.")
        actual = self.identity()
        mismatches = {key: actual[key] for key, expected in self.profile["tested_identity"].items() if actual[key] != expected}
        if mismatches:
            raise RuntimeError("Unsupported hardware/OS; no changes made: " + json.dumps(mismatches))
        if actual["ro.build.fingerprint"] != self.profile["tested_fingerprint"]:
            raise RuntimeError("Untested firmware fingerprint; inspect and review a separate profile before applying changes.")
        return actual

    def packages(self):
        return set(re.findall(r"^package:(.+)$", self.shell("pm", "list", "packages"), re.M))

    def package_state(self, package):
        text = self.shell("dumpsys", "package", package)
        match = re.search(r"User 0:.*?\benabled=(\d+)", text)
        if not match:
            raise RuntimeError("Cannot read original enabled state: " + package)
        return int(match.group(1))

    def launch(self, package):
        output = self.shell("cmd", "package", "resolve-activity", "--brief", "-a", "android.intent.action.MAIN",
                            "-c", "android.intent.category.LEANBACK_LAUNCHER", "-p", package)
        matches = [line for line in output.splitlines() if line.startswith(package + "/")]
        if len(matches) != 1:
            raise RuntimeError("No single enabled TV launcher activity for " + package)
        output = self.shell("am", "start", "-W", "-n", matches[0])
        if "Error:" in output or "Status: timeout" in output:
            raise RuntimeError(output)
        return output

    def ui(self):
        self.shell("uiautomator", "dump", "/data/local/tmp/grunkel-ui.xml")
        return ET.fromstring(self.shell("cat", "/data/local/tmp/grunkel-ui.xml"))

    def screenshot(self):
        self.require_serial()
        data = self.adb("-s", self.serial, "exec-out", "screencap", "-p")
        start = data.find(bytes.fromhex("89504e470d0a1a0a"))
        if start < 0:
            raise RuntimeError("No PNG returned; protected screens may not be capturable. No image saved.")
        path = ROOT / "screenshots" / (stamp() + ".png")
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data[start:])
        return str(path)


def application_locales(tv, package):
    output = tv.shell("cmd", "locale", "get-app-locales", package, "--user", "0")
    match = re.search(r"are \[(.*?)\]", output)
    if not match:
        raise RuntimeError("Cannot read application locales: " + package)
    return ",".join(tag.strip().replace("_", "-") for tag in match.group(1).split(",") if tag.strip())


def journal(tv, kind):
    path = ROOT / "backups" / stamp() / "changes.json"
    state = {"format": 1, "kind": kind, "serial": tv.serial, "identity": tv.guard(), "changes": [], "complete": False}
    write_json(path, state)
    return path, state


def perform(tv, path, state, change, command, verify):
    change["status"] = "pending"
    state["changes"].append(change)
    write_json(path, state)  # Persist the original value before sending a mutation.
    output = tv.shell(*command)
    if not verify():
        raise RuntimeError("Change could not be verified. Restore with rollback --journal " + str(path) + "\n" + output)
    change["status"] = "applied"
    write_json(path, state)


def apply_profile(tv):
    actual = tv.guard()
    present = tv.packages()
    missing = set(tv.profile["required_packages"]) - present
    if missing:
        raise RuntimeError("Required packages missing: " + ", ".join(sorted(missing)))
    prohibited = set(tv.profile["disable_packages"]) & (set(tv.profile["protected_packages"]) | {component.split("/")[0] for component in HOME_LAUNCHERS.values()})
    if prohibited:
        raise RuntimeError("Profile attempts to disable a protected package: " + str(prohibited))
    path, state = journal(tv, "privacy-performance")
    print("Rollback journal:", path, flush=True)
    # Snapshot memory while on the same idle HOME screen before applying the profile.
    before = tv.shell("cat", "/proc/meminfo")
    path.with_name("memory-before.txt").write_text(before + "\n")
    for package, reason in tv.profile["disable_packages"].items():
        if package not in present:
            print("skip missing", package, flush=True)
            continue
        original = tv.package_state(package)
        if original in (2, 3, 4):
            print("skip already disabled", package, flush=True)
            continue
        perform(tv, path, state, {"type": "package", "package": package, "before": original, "after": 3, "reason": reason},
                ["pm", "disable-user", "--user", "0", package], lambda p=package: tv.package_state(p) == 3)
        print("disabled", package, flush=True)
    for item in tv.profile["settings"]:
        namespace, key, target = item["namespace"], item["key"], item["value"]
        original = tv.shell("settings", "get", namespace, key)
        if original == target:
            continue
        perform(tv, path, state, {"type": "setting", "namespace": namespace, "key": key, "before": original, "after": target},
                ["settings", "put", namespace, key, target], lambda n=namespace, k=key, v=target: tv.shell("settings", "get", n, k) == v)
    state["complete"] = True
    write_json(path, state)
    path.with_name("memory-after.txt").write_text(tv.shell("cat", "/proc/meminfo") + "\n")
    print("Profile applied and values verified. This does not establish zero telemetry or a speedup.")


def restore(tv, filename):
    path = Path(filename).resolve()
    state = json.loads(path.read_text())
    actual = tv.guard()
    if state["serial"] != tv.serial or state["identity"] != actual:
        raise RuntimeError("The rollback journal belongs to a different device/identity.")
    # Every potentially applied operation, including an interrupted pending operation, is restored.
    commands = {0: "default-state", 1: "enable", 2: "disable", 3: "disable-user", 4: "disable-until-used"}
    for change in reversed(state["changes"]):
        if change.get("status") == "restored":
            continue
        if change["type"] == "package":
            package, original = change["package"], change["before"]
            if original not in commands:
                raise RuntimeError("Unknown saved package state; no state guessed.")
            tv.shell("pm", commands[original], "--user", "0", package)
            if tv.package_state(package) != original:
                raise RuntimeError("Package restoration failed: " + package)
        elif change["type"] == "setting":
            ns, key, original = change["namespace"], change["key"], change["before"]
            tv.shell("settings", "delete" if original == "null" else "put", ns, key, *([] if original == "null" else [original]))
            if tv.shell("settings", "get", ns, key) != original:
                raise RuntimeError("Setting restoration failed: " + key)
        elif change["type"] == "airplay":
            output = tv.shell("am", "broadcast", "-n", "io.github.jqssun.airplay/.SettingsReceiver", "-a",
                              "io.github.jqssun.airplay.SET_SETTING", "--es", "key", change["key"], "--es", "value", change["before"])
            if "result=-1" not in output or airplay_values(tv).get(change["key"]) != change["before"]:
                raise RuntimeError("AirPlay restoration failed: " + output)
        elif change["type"] == "install-source":
            package, original = change["package"], change["before"]
            if package not in INSTALL_SOURCES.values() or original not in APP_OP_MODES:
                raise RuntimeError("Unsupported installation-source journal entry; nothing guessed.")
            tv.shell("cmd", "appops", "set", "--user", "0", package, INSTALL_OP, original)
            if install_source_mode(tv, package) != original:
                raise RuntimeError("Installation-source restoration failed: " + package)
        elif change["type"] == "file-picker-access":
            if change["before"] not in APP_OP_MODES:
                raise RuntimeError("Invalid original file-picker storage mode.")
            tv.shell("cmd", "appops", "set", "--user", "0", FILES_PACKAGE, FILES_OP, change["before"])
            if files_access_mode(tv) != change["before"]:
                raise RuntimeError("File-picker storage permission restoration failed.")
        elif change["type"] == "photo-permission":
            if not isinstance(change["before"], bool):
                raise RuntimeError("Invalid photo permission journal.")
            tv.shell("pm", "grant" if change["before"] else "revoke", "--user", "0", PHOTO_PACKAGE, "android.permission.READ_MEDIA_IMAGES")
            if photo_permission(tv) != change["before"]:
                raise RuntimeError("Photo read permission restoration failed.")
        elif change["type"] == "app-locales":
            tv.shell("cmd", "locale", "set-app-locales", change["package"], "--user", "0", "--locales", change["before"])
            if application_locales(tv, change["package"]) != change["before"]:
                raise RuntimeError("Application locale restoration failed: " + change["package"])
        elif change["type"] == "launcher-selection":
            before = change["before"]
            if before is not None and (not isinstance(before, dict) or before.get("name") not in HOME_LAUNCHERS or not isinstance(before.get("fingerprint"), str)):
                raise RuntimeError("Invalid saved launcher choice in journal.")
            data = launcher_state()
            if before is None:
                data["devices"].pop(tv.serial, None)
            else:
                data["devices"][tv.serial] = before
            if not data["devices"] and change.get("file_existed") is False:
                if LAUNCHER_STATE.exists():
                    LAUNCHER_STATE.unlink()
            else:
                write_json(LAUNCHER_STATE, data)
        elif change["type"] == "home":
            output = tv.shell("cmd", "package", "set-home-activity", "--user", "0", change["before"])
            resolved = tv.shell("cmd", "package", "resolve-activity", "--brief", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
            if "Success" not in output or change["before"] not in resolved:
                raise RuntimeError("Home restoration failed: " + output)
        else:
            raise RuntimeError("Unknown journal operation; refusing to execute it.")
        change["status"] = "restored"
        write_json(path, state)
    state["restored_at"] = dt.datetime.now().astimezone().isoformat()
    write_json(path, state)
    print("Restored original values recorded in", path)


def locks():
    return json.loads((ROOT / "apps.lock.json").read_text())["apps"]


def fetch_apps(names):
    unknown = set(names) - set(locks())
    if unknown:
        raise ValueError("Unknown apps: " + ", ".join(sorted(unknown)))
    selected = set(names or DEFAULT_APPS)
    for name, app in locks().items():
        if name not in selected:
            continue
        target = ROOT / "downloads" / app["filename"]
        target.parent.mkdir(exist_ok=True)
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != app["sha256"]:
            tmp = target.with_suffix(".part")
            request = Request(app["url"], headers={"User-Agent": "Grunkel-LED-3211GOO-setup"})
            try:
                with urlopen(request, timeout=60) as source, tmp.open("wb") as dest:
                    shutil.copyfileobj(source, dest)
                if hashlib.sha256(tmp.read_bytes()).hexdigest() != app["sha256"]:
                    raise RuntimeError("SHA-256 mismatch; APK will not be installed: " + name)
                tmp.replace(target)
            finally:
                if tmp.exists():
                    tmp.unlink()
        print(name, "SHA-256 OK", target)


def verify_installed_apk(tv, app):
    paths = [line[len("package:"):] for line in tv.shell("pm", "path", app["package"]).splitlines() if line.startswith("package:")]
    if len(paths) != 1:
        raise RuntimeError("Expected one pinned monolithic APK; inspect the installed variant: " + app["package"])
    actual = tv.shell("sha256sum", paths[0]).split()[0]
    if actual != app["sha256"]:
        raise RuntimeError("Installed APK differs from the pinned file; review separately: " + app["package"])


def install_apps(tv, names):
    unknown = set(names) - set(locks())
    if unknown:
        raise ValueError("Unknown apps: " + ", ".join(sorted(unknown)))
    tv.guard()
    apps = locks()
    selected = names or list(default_apps(tv))
    path, state = journal(tv, "install-apps")
    print("Installation journal:", path, flush=True)
    present = tv.packages()
    for name in selected:
        if name not in apps:
            raise ValueError("Unknown app: " + name)
        app = apps[name]
        target = ROOT / "downloads" / app["filename"]
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != app["sha256"]:
            raise RuntimeError("Verified APK missing. Run download-apps first: " + name)
        if app["package"] in present:
            output = tv.shell("dumpsys", "package", app["package"])
            match = re.search(r"\bversionCode=(\d+)", output)
            if match and int(match.group(1)) == app["version_code"]:
                verify_installed_apk(tv, app)
                print("skip installed version; APK SHA-256 verified", name, flush=True)
                continue
            raise RuntimeError("A different version already exists; review the update separately: " + name)
        # New installations are recorded separately; rollback never uninstalls apps or deletes data.
        record = {"package": app["package"], "version": app["version"], "status": "pending"}
        state.setdefault("installations", []).append(record)
        write_json(path, state)
        output = tv.adb("-s", tv.serial, "install", "--no-streaming", str(target), timeout=120).decode()
        if "Success" not in output:
            raise RuntimeError(output)
        verify_installed_apk(tv, app)
        record["status"] = "installed"
        write_json(path, state)
        print("installed", name, flush=True)
    state["complete"] = True
    write_json(path, state)


def airplay_values(tv):
    response = tv.shell("am", "broadcast", "-n", "io.github.jqssun.airplay/.SettingsReceiver", "-a", "io.github.jqssun.airplay.LIST_SETTINGS")
    match = re.search(r'data="(\{.*\})"', response)
    if not match:
        raise RuntimeError("Cannot verify AirPlay settings: " + response)
    data = match.group(1)
    try:
        values = json.loads(data)
    except json.JSONDecodeError:
        values = json.loads(data.replace('\\"', '"'))
    return {key: str(item["value"]).lower() if isinstance(item["value"], bool) else str(item["value"])
            for key, item in values.items()}


def airplay_config(tv):
    tv.guard()
    if "io.github.jqssun.airplay" not in tv.packages():
        raise RuntimeError("Install the pinned AirPlay app first.")
    tv.launch("io.github.jqssun.airplay")
    original = airplay_values(tv)
    desired = {"server_name": "Grunkel LED-3211GOO", "resolution": "1280x720", "max_fps": "30",
               "require_pin": "true", "debug_enabled": "false", "benchmark_log": "false",
               "idle_preview": "false", "boot_auto_start": "true", "run_in_background": "true"}
    path, state = journal(tv, "airplay-settings")
    print("Rollback journal:", path, flush=True)
    for key, value in desired.items():
        before = original[key]
        before = str(before).lower() if isinstance(before, bool) else str(before)
        if before == value:
            continue
        change = {"type": "airplay", "key": key, "before": before, "after": value, "status": "pending"}
        state["changes"].append(change); write_json(path, state)
        output = tv.shell("am", "broadcast", "-n", "io.github.jqssun.airplay/.SettingsReceiver", "-a",
                          "io.github.jqssun.airplay.SET_SETTING", "--es", "key", key, "--es", "value", value)
        if "result=-1" not in output or airplay_values(tv).get(key) != value:
            raise RuntimeError("AirPlay setting failed; restore the journal: " + output)
        change["status"] = "applied"; write_json(path, state)
    state["complete"] = True; write_json(path, state)
    print(tv.shell("am", "broadcast", "-n", "io.github.jqssun.airplay/.SettingsReceiver", "-a", "io.github.jqssun.airplay.LIST_SETTINGS"))


def home_config(tv, stock_mode=False):
    tv.guard()
    name, selected = configured_home(tv)
    target = "com.google.android.tvlauncher/.MainActivity" if stock_mode else selected
    stock = "com.google.android.tvlauncher"
    if not stock_mode:
        if selected.split("/")[0] not in tv.packages():
            raise RuntimeError("Install the configured launcher and finish its welcome screen first.")
        verify_installed_apk(tv, locks()[name])
        # Validate the local state before making any TV changes.
        saved = launcher_state()["devices"].get(tv.serial)
        remember = saved != {"name": name, "fingerprint": tv.profile["tested_fingerprint"]}
    else:
        remember = False
    current = tv.shell("cmd", "package", "resolve-activity", "--brief", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
    components = [line for line in current.splitlines() if re.fullmatch(r"[A-Za-z0-9_.$]+/[A-Za-z0-9_.$]+", line)]
    if len(components) != 1:
        raise RuntimeError("Cannot identify the original HOME activity; nothing changed.")
    before_home = components[0]
    before_package = tv.package_state(stock)
    tv_matches = before_home == target and ((stock_mode and before_package in (0, 1)) or (not stock_mode and before_package in (2, 3, 4)))
    if tv_matches and not remember:
        print("Requested HOME and launcher state already configured. No changes.")
        return
    if not stock_mode and not tv_matches:
        tv.launch(selected.split("/")[0])
    path, state = journal(tv, "home-screen")
    print("Rollback journal:", path, flush=True)
    if not tv_matches:
        # Rollback enables the old launcher before restoring its HOME role.
        change = {"type": "home", "before": before_home, "after": target, "status": "pending"}
        state["changes"].append(change); write_json(path, state)
        if stock_mode and before_package in (2, 3, 4):
            perform(tv, path, state, {"type": "package", "package": stock, "before": before_package, "after": 1},
                    ["pm", "enable", "--user", "0", stock], lambda: tv.package_state(stock) == 1)
        elif not stock_mode and before_package not in (2, 3, 4):
            perform(tv, path, state, {"type": "package", "package": stock, "before": before_package, "after": 3},
                    ["pm", "disable-user", "--user", "0", stock], lambda: tv.package_state(stock) == 3)
        output = tv.shell("cmd", "package", "set-home-activity", "--user", "0", target)
        resolved = tv.shell("cmd", "package", "resolve-activity", "--brief", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
        if "Success" not in output or target not in resolved:
            raise RuntimeError("HOME was not verified. Restore the recorded journal: " + str(path))
        change["status"] = "applied"; write_json(path, state)
    if not stock_mode:
        save_launcher_selection(tv, path, state, name)
    state["complete"] = True; write_json(path, state)
    if not tv_matches:
        tv.shell("input", "keyevent", "KEYCODE_HOME")
    print("HOME verified:", target)


def performance(tv, label):
    tv.guard()
    _, home = configured_home(tv)
    home_package = home.split("/")[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", label):
        raise ValueError("Use a simple label such as before or after.")
    time.sleep(3)
    folder = ROOT / "diagnostics" / (stamp() + "-" + label)
    folder.mkdir(parents=True)
    foreground = tv.shell("dumpsys", "activity", "activities")
    (folder / "activities-before.txt").write_text(foreground + "\n")
    resumed = [line for line in foreground.splitlines() if "mResumedActivity" in line or "topResumedActivity" in line]
    if not resumed or not all(home_package in line for line in resumed):
        raise RuntimeError("Configured HOME was not idle; snapshot refused. Close casting/apps before retrying. Evidence: " + str(folder))
    for name, command in [("memory", ["cat", "/proc/meminfo"]), ("cpu", ["dumpsys", "cpuinfo"]),
                          ("vmstat", ["vmstat", "1", "5"]), ("home-memory", ["dumpsys", "meminfo", home_package])]:
        (folder / (name + ".txt")).write_text(tv.shell(*command) + "\n")
    foreground_after = tv.shell("dumpsys", "activity", "activities")
    (folder / "activities-after.txt").write_text(foreground_after + "\n")
    resumed_after = [line for line in foreground_after.splitlines() if "mResumedActivity" in line or "topResumedActivity" in line]
    if not resumed_after or not all(home_package in line for line in resumed_after):
        raise RuntimeError("Foreground changed during sampling; measurements are not comparable: " + str(folder))
    print(folder)


def verify_configuration(tv):
    """Read current configuration; never repair drift or change the HOME role."""
    tv.guard()
    present = tv.packages()
    report = {"checks": {}, "installed_apks": {}, "factory_reset_resistant": False,
              "scope": "Profile/package states, APK-source default-off modes, HOME and pinned APKs; language properties only. PIN, UI layout, full translations and playback are separate checks."}
    checks = report["checks"]
    checks["required_packages"] = {p: p in present for p in tv.profile["required_packages"]}
    states = {p: tv.package_state(p) for p in set(tv.profile["protected_packages"]) | set(tv.profile["disable_packages"]) if p in present}
    checks["protected_packages_enabled"] = {p: states[p] not in (2, 3, 4) for p in tv.profile["protected_packages"] if p in states}
    checks["optional_packages_disabled"] = {p: states[p] in (2, 3, 4) for p in tv.profile["disable_packages"] if p in states}
    report["installation_sources"] = installer_status(tv)
    checks["apk_sources_default_off"] = report["installation_sources"]["default_off"]
    checks["system_installer_enabled"] = report["installation_sources"]["system_installer_enabled"]
    report["settings"] = []
    for item in tv.profile["settings"]:
        actual = tv.shell("settings", "get", item["namespace"], item["key"])
        report["settings"].append({"namespace": item["namespace"], "key": item["key"], "expected": item["value"], "actual": actual})
    checks["settings_match"] = all(item["actual"] == item["expected"] for item in report["settings"])
    home = tv.shell("cmd", "package", "resolve-activity", "--brief", "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME")
    report["home"] = home.splitlines()[-1] if home else ""
    report["configured_launcher"], report["expected_home"] = configured_home(tv)
    checks["configured_home"] = report["home"] == report["expected_home"]
    apps = locks()
    checks["default_apps_enabled"] = {name: apps[name]["package"] in present and tv.package_state(apps[name]["package"]) not in (2, 3, 4) for name in default_apps(tv)}
    for name in default_apps(tv):
        app = apps[name]
        try:
            verify_installed_apk(tv, app)
            report["installed_apks"][name] = {"matches_pin": True}
        except RuntimeError as error:
            report["installed_apks"][name] = {"matches_pin": False, "error": str(error)}
    checks["pinned_apks_match"] = all(item["matches_pin"] for item in report["installed_apks"].values())
    report["language"] = {
        "system_locales": tv.shell("settings", "get", "system", "system_locales"),
        "persistent_locale": tv.shell("getprop", "persist.sys.locale"),
        "factory_property": tv.shell("getprop", "ro.product.locale"),
        "projectivy_override": application_locales(tv, "com.spocky.projengmenu") if "com.spocky.projengmenu" in present else None,
        "factory_reset_default_verified": False,
    }
    report["timezone"] = tv.shell("getprop", "persist.sys.timezone")
    if PHOTO_PACKAGE in present:
        report["photos"] = photo_status(tv)
        checks["photo_screensaver_policy"] = report["photos"]["timing_matches"]
        checks["photo_read_permission"] = report["photos"].get("app", {}).get("photo_access_granted") is True
        checks["photo_interval_30_seconds"] = report["photos"].get("app", {}).get("interval_ms") == 30000
        # USB removal is expected during ordinary use and must not fail global verification.
        report["photos"]["usb_presence_required_for_verify"] = False
    values = []
    for value in checks.values():
        values.extend(value.values() if isinstance(value, dict) else [value])
    report["ok"] = all(values)
    return report



def photo_artifact():
    path = ROOT / "downloads/grunkel-photos-build.local.json"
    if not path.exists():
        raise RuntimeError("Build the original offline photo app first: make photos-build")
    data = json.loads(path.read_text())
    apk = Path(data["apk"]).resolve()
    try:
        apk.relative_to((ROOT / "downloads").resolve())
    except ValueError:
        raise RuntimeError("Photo APK must be inside the private downloads folder.")
    if data.get("package") != PHOTO_PACKAGE or data.get("network_permission") is not False or not apk.is_file() or hashlib.sha256(apk.read_bytes()).hexdigest() != data["sha256"]:
        raise RuntimeError("Original photo build metadata/hash mismatch; nothing installed.")
    return data, apk


def install_photos(tv):
    tv.guard()
    data, apk = photo_artifact()
    before = PHOTO_PACKAGE in tv.packages()
    if before:
        try:
            verify_installed_apk(tv, {"package": PHOTO_PACKAGE, "sha256": data["sha256"]})
            print("Offline photo app already matches this local signed build.")
            return
        except RuntimeError:
            pass
    path, state = journal(tv, "photo-app-install")
    record = {"package": PHOTO_PACKAGE, "before_installed": before, "after_sha256": data["sha256"], "status": "pending"}
    state["installations"] = [record]
    write_json(path, state)
    if before:
        remote = tv.shell("pm", "path", PHOTO_PACKAGE).removeprefix("package:")
        if "\n" in remote or not remote.startswith("/data/app/"):
            raise RuntimeError("Cannot identify previous monolithic photo APK.")
        tv.adb("-s", tv.serial, "pull", remote, str(path.with_name("previous-photo.apk")))
    output = tv.adb("-s", tv.serial, "install", "--no-streaming", "-r", str(apk), timeout=120).decode()
    if "Success" not in output:
        raise RuntimeError(output)
    verify_installed_apk(tv, {"package": PHOTO_PACKAGE, "sha256": data["sha256"]})
    record["status"] = "installed"
    state["complete"] = True
    write_json(path, state)
    print("Installed original offline photo app; signed local APK SHA-256 verified. No USB files or APK-source permissions changed.")


def shortcut_artifacts():
    pointer = ROOT / "downloads/grunkel-shortcuts-build.local.json"
    if not pointer.is_file():
        raise RuntimeError("Build the original shortcuts first: make shortcuts-build")
    data = json.loads(pointer.read_text())
    artifacts = data.get("artifacts", {})
    if data.get("schema") != 1 or set(artifacts) != set(SHORTCUT_PACKAGES):
        raise RuntimeError("Shortcut build metadata is incomplete.")
    for name, app in artifacts.items():
        apk = Path(app["apk"]).resolve()
        if not apk.is_relative_to((ROOT / "downloads").resolve()) or not apk.is_file():
            raise RuntimeError("Shortcut APK must be inside private downloads.")
        if app.get("package") != SHORTCUT_PACKAGES[name] or app.get("permissions") != [] or hashlib.sha256(apk.read_bytes()).hexdigest() != app.get("sha256"):
            raise RuntimeError("Shortcut package, permissions or file hash mismatch; nothing installed.")
    return artifacts


def install_shortcuts(tv):
    tv.guard()
    artifacts = shortcut_artifacts()  # Preflight both APKs before the first mutation.
    path, state = journal(tv, "shortcut-app-install")
    state["installations"] = []
    present = tv.packages()
    for name, app in artifacts.items():
        package = app["package"]
        if package in present:
            try:
                verify_installed_apk(tv, app)
                print(name + " shortcut already matches; skipped.")
                continue
            except RuntimeError:
                pass
        record = {"package": package, "before_installed": package in present, "after_sha256": app["sha256"], "status": "pending"}
        state["installations"].append(record); write_json(path, state)
        if package in present:
            remote = tv.shell("pm", "path", package).removeprefix("package:")
            if "\n" in remote or not remote.startswith("/data/app/"):
                raise RuntimeError("Cannot identify previous monolithic shortcut APK.")
            tv.adb("-s", tv.serial, "pull", remote, str(path.with_name("previous-" + name + ".apk")))
        output = tv.adb("-s", tv.serial, "install", "--no-streaming", "-r", app["apk"], timeout=120).decode()
        if "Success" not in output:
            raise RuntimeError(output)
        verify_installed_apk(tv, app)
        record["status"] = "installed"; write_json(path, state)
    state["complete"] = True; write_json(path, state)
    print("Original offline input/USB shortcuts installed and SHA-256 verified. No storage grants, USB writes, input tuning or HOME changes.")


def shortcut_status(tv):
    tv.guard()
    present = tv.packages()
    return {name: {"installed": package in present,
                   "enabled": tv.package_state(package) not in (2, 3, 4) if package in present else False}
            for name, package in SHORTCUT_PACKAGES.items()}


def photo_permission(tv):
    dump = tv.shell("dumpsys", "package", PHOTO_PACKAGE)
    match = re.search(r"User 0:(.*?)(?=\n\s*User \d+:|\Z)", dump, re.S)
    if not match or "android.permission.READ_MEDIA_IMAGES" not in dump:
        raise RuntimeError("Cannot read photo application permission state.")
    values = re.findall(r"android.permission.READ_MEDIA_IMAGES: granted=(true|false)", match[1])
    if len(values) > 1:
        raise RuntimeError("Ambiguous photo permission state.")
    return bool(values and values[0] == "true")


def photo_access(tv):
    tv.guard()
    data, _ = photo_artifact()
    verify_installed_apk(tv, {"package": PHOTO_PACKAGE, "sha256": data["sha256"]})
    if photo_permission(tv):
        return
    path, state = journal(tv, "photo-read-access")
    perform(tv, path, state, {"type": "photo-permission", "before": False, "after": True},
            ["pm", "grant", "--user", "0", PHOTO_PACKAGE, "android.permission.READ_MEDIA_IMAGES"],
            lambda: photo_permission(tv))
    state["complete"] = True
    write_json(path, state)
    print("Read-photos permission granted with original-value journal:", path)


def photo_status(tv):
    tv.guard()
    settings = [{"namespace": ns, "key": key, "expected": value,
                 "actual": tv.shell("settings", "get", ns, key)} for ns, key, value in PHOTO_POLICY]
    report = {"installed": PHOTO_PACKAGE in tv.packages(), "settings": settings,
              "timing_matches": all(item["actual"] == item["expected"] for item in settings),
              "idle_minutes": 5, "show_minutes": 25, "sleep_after_total_minutes": 30,
              "note": "Values are configuration, not proof of a completed 30-minute physical cycle."}
    if report["installed"]:
        output = tv.shell("am", "broadcast", "-n", PHOTO_PACKAGE + "/.StatusReceiver", "-a", PHOTO_PACKAGE + ".STATUS")
        match = re.search(r'data="(\{.*\})"', output)
        if "result=-1" not in output or not match:
            raise RuntimeError("Cannot read redacted photo app status; no path guessed.")
        try:
            report["app"] = json.loads(match[1])
        except json.JSONDecodeError:
            report["app"] = json.loads(match[1].replace('\\"', '"'))
    return report


def apply_photo_policy(tv):
    report = photo_status(tv)
    if not report["installed"] or not report.get("app", {}).get("can_preview"):
        raise RuntimeError("Choose a readable USB photo folder with make photos-choose, then preview it before applying timing.")
    data, _ = photo_artifact()
    verify_installed_apk(tv, {"package": PHOTO_PACKAGE, "sha256": data["sha256"]})
    path, state = journal(tv, "photo-screensaver")
    print("Rollback journal:", path, flush=True)
    for ns, key, target in PHOTO_POLICY:
        original = tv.shell("settings", "get", ns, key)
        if original == target:
            continue
        perform(tv, path, state, {"type": "setting", "namespace": ns, "key": key, "before": original, "after": target},
                ["settings", "put", ns, key, target], lambda n=ns, k=key, v=target: tv.shell("settings", "get", n, k) == v)
    state["complete"] = True
    write_json(path, state)
    print(json.dumps(photo_status(tv), ensure_ascii=False, indent=2))


def install_source_mode(tv, package):
    if package not in INSTALL_SOURCES.values():
        raise ValueError("Only reviewed APK sources are supported.")
    text = tv.shell("cmd", "appops", "get", "--user", "0", package, INSTALL_OP)
    if "Uid mode:" in text:
        raise RuntimeError("UID-wide app-op override detected; review it before changing package modes.")
    modes = re.findall(r"^REQUEST_INSTALL_PACKAGES: (allow|ignore|deny|default|foreground)(?=;|\s|$)", text, re.M)
    if len(modes) == 1:
        return modes[0]
    if not modes and re.search(r"^No operations\.$", text, re.M):
        default = re.search(r"^Default mode: (allow|ignore|deny|default|foreground)\s*$", text, re.M)
        if default:
            return default[1]
    raise RuntimeError("Cannot read the original installation-source mode; no value guessed.")


def installer_status(tv):
    tv.guard()
    present = tv.packages()
    sources = {}
    for name, package in INSTALL_SOURCES.items():
        if package not in present:
            continue
        sources[name] = {"package": package, "mode": install_source_mode(tv, package)}
    native = "com.google.android.packageinstaller"
    return {"sources": sources,
            "default_off": all(item["mode"] in ("deny", "ignore") for item in sources.values()),
            "system_installer_enabled": native in present and tv.package_state(native) not in (2, 3, 4),
            "scope": "Per-source APK requests from installed Projectivy, Plume, Material Files and TV Bro; ADB and Play Store remain available."}


def configure_installer(tv, enabled):
    before = installer_status(tv)
    if not before["system_installer_enabled"]:
        raise RuntimeError("Factory APK installer is unavailable; no package state changed.")
    if enabled and "projectivy" not in before["sources"]:
        raise RuntimeError("Optional Projectivy APK picker is not installed; no modes changed. Use ADB or installer settings explicitly.")
    for item in before["sources"].values():
        package = item["package"]
        if "android.permission.REQUEST_INSTALL_PACKAGES" not in tv.shell("dumpsys", "package", package):
            raise RuntimeError("Reviewed source does not declare APK installation permission: " + package)
    path, state = journal(tv, "installation-sources")
    print("Rollback journal:", path, flush=True)
    # Keep the browser off; optional enablement applies only to Projectivy.
    for name in ("browser", "plume", "files", "projectivy"):
        if name not in before["sources"]:
            continue
        package = INSTALL_SOURCES[name]
        target = "allow" if enabled and name == "projectivy" else "deny"
        original = before["sources"][name]["mode"]
        if original == target:
            continue
        perform(tv, path, state,
                {"type": "install-source", "package": package, "before": original, "after": target},
                ["cmd", "appops", "set", "--user", "0", package, INSTALL_OP, target],
                lambda p=package, v=target: install_source_mode(tv, p) == v)
    state["complete"] = True
    write_json(path, state)
    report = installer_status(tv)
    if enabled:
        if any(item["mode"] != ("allow" if name == "projectivy" else "deny") for name, item in report["sources"].items()):
            raise RuntimeError("Installation-source enablement did not match the reviewed scope.")
    elif not report["default_off"]:
        raise RuntimeError("Installation sources did not switch off.")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def files_access_mode(tv):
    text = tv.shell("cmd", "appops", "get", "--user", "0", FILES_PACKAGE, FILES_OP)
    if "Uid mode:" in text:
        raise RuntimeError("UID-wide storage override detected; review it before changing package mode.")
    modes = re.findall(r"^MANAGE_EXTERNAL_STORAGE: (allow|ignore|deny|default|foreground)(?=;|\s|$)", text, re.M)
    if len(modes) == 1:
        return modes[0]
    if not modes and re.search(r"^No operations\.$", text, re.M):
        default = re.search(r"^Default mode: (allow|ignore|deny|default|foreground)\s*$", text, re.M)
        if default:
            return default[1]
    raise RuntimeError("Cannot read original all-files access; no mode guessed.")


def files_access_status(tv):
    tv.guard()
    installed = FILES_PACKAGE in tv.packages()
    mode = files_access_mode(tv) if installed else None
    return {"installed": installed, "mode": mode, "allowed": mode == "allow",
            "scope": "Optional Material Files shared-storage access, including removable media; not private app data/root/installation permission."}


def configure_files_access(tv, enabled):
    tv.guard()
    if FILES_PACKAGE not in tv.packages():
        raise RuntimeError("Install the optional pinned files app first.")
    verify_installed_apk(tv, locks()["files"])
    before = files_access_mode(tv)
    after = "allow" if enabled else "deny"
    if before == after:
        print("All-files access already matches; no changes.")
        return
    path, state = journal(tv, "file-picker-storage-access")
    perform(tv, path, state, {"type": "file-picker-access", "before": before, "after": after},
            ["cmd", "appops", "set", "--user", "0", FILES_PACKAGE, FILES_OP, after],
            lambda: files_access_mode(tv) == after)
    state["complete"] = True; write_json(path, state)
    print("Rollback journal:", path)
    print(json.dumps(files_access_status(tv), indent=2))


def installer_settings(tv):
    tv.guard()
    # This OEM shows an empty list for a package: URI; use its verified global list.
    output = tv.shell("am", "start", "-W", "-a", "android.settings.MANAGE_UNKNOWN_APP_SOURCES")
    if "Error:" in output or "Status: timeout" in output:
        raise RuntimeError(output)
    print(output)
    print("Only settings were opened; no installation permission was enabled.")


def internal_storage_status(tv):
    """Read capacity without listing media, cleaning caches, or changing packages."""
    tv.guard()
    rows = []
    for line in tv.shell("df", "-k", "/data").splitlines():
        fields = line.split()
        if len(fields) == 6 and all(re.fullmatch(r"\d+", v) for v in fields[1:4]) and re.fullmatch(r"\d+%", fields[4]):
            total, used, available = map(int, fields[1:4])
            if total <= 0 or used + available > total or int(fields[4][:-1]) > 100:
                raise RuntimeError("Inconsistent data capacity; no storage size guessed.")
            rows.append({"total_KiB": total, "used_KiB": used, "available_KiB": available,
                         "total_GiB": round(total / 1048576, 3), "available_GiB": round(available / 1048576, 3),
                         "available_percent": round(100 * available / total, 2),
                         "calculation": "GiB = KiB / 1048576; available_percent = 100 * available_KiB / total_KiB"})
    if len(rows) != 1:
        raise RuntimeError("No unambiguous data capacity report; no paths or content inspected.")
    mem = tv.shell("cat", "/proc/meminfo")
    memory = {}
    for key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
        found = re.findall(r"^" + key + r":\s+(\d+) kB$", mem, re.M)
        if len(found) != 1:
            raise RuntimeError("Incomplete memory report: " + key)
        memory[key + "_KiB"] = int(found[0])
    firmware = {}
    for line in tv.shell("cat", "/proc/mounts").splitlines():
        fields = line.split()
        if len(fields) >= 4 and fields[1] in ("/", "/system", "/vendor", "/product"):
            firmware[fields[1]] = {"filesystem": fields[2], "read_only": "ro" in fields[3].split(",")}
    return {"observed_at": dt.datetime.now().astimezone().isoformat(), "data_partition": rows[0],
            "memory": memory, "low_ram_property": tv.shell("getprop", "ro.config.low_ram"),
            "firmware_mounts": firmware, "read_only_audit": True,
            "note": "Live available bytes change with use. Data partition is not total flash capacity. Disabling an app leaves APK files; read-only firmware bytes do not become data space. No cleanup/uninstall/reset/USB operations sent."}


def portable_storage_status(tv):
    """Read Android public-volume states; never inspect the drive contents.

    Public volumes may include USB or SD. This does not prove a USB transport,
    media-format compatibility, or implement a live Projectivy card.
    AOSP Android 14 Sm.runListVolumes prints: id environment_state fsUuid.
    """
    tv.guard()
    output = tv.shell("sm", "list-volumes", "public")
    known = {"unmounted", "checking", "mounted", "mounted_ro", "ejecting",
             "unmountable", "removed", "bad_removal", "unknown", "shared"}
    states = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) != 3 or not re.fullmatch(r"public:[0-9]+,[0-9]+", fields[0]) or fields[1] not in known:
            # Do not echo raw output: it can contain an owner's drive ID or label.
            raise RuntimeError("Unrecognized storage status; availability is unknown. No media player opened.")
        states.append(fields[1])
    readable = sum(state in ("mounted", "mounted_ro") for state in states)
    if readable:
        availability = "ready"
    elif any(state in ("unmountable", "bad_removal", "unknown") for state in states):
        availability = "error"
    elif any(state in ("checking", "ejecting", "shared") for state in states):
        availability = "busy"
    elif not states or all(state == "removed" for state in states):
        availability = "absent"
    else:
        availability = "not_mounted"
    return {"source": "sm list-volumes public", "kind": "portable_storage_usb_or_sd",
            "availability": availability, "readable_volumes": readable,
            "volume_states": sorted(states), "can_open": bool(readable),
            "projectivy_dynamic_card_implemented": False}


def open_portable_storage(tv):
    status = portable_storage_status(tv)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    if not status["can_open"]:
        raise RuntimeError("No readable portable drive. Connect a drive and wait for Android to mount it; nothing opened.")
    package = "com.mediatek.wwtv.mediaplayer"
    if package not in tv.packages() or tv.package_state(package) in (2, 3, 4):
        raise RuntimeError("Factory media player is unavailable; no package state changed.")
    print(tv.launch(package))
    print("Factory media browser opened. Select the drive with the remote; its contents were not inspected by this command.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", help="Exact ADB serial/IP:port; no network scan is performed")
    parser.add_argument("--profile", default=str(DEFAULT_PROFILE))
    parser.add_argument("--launcher", choices=sorted(HOME_LAUNCHERS), help="Launcher for install/HOME/verify; successful home remembers it per device")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("launchers", help="List pinned launcher options without contacting a TV")
    for name in ("doctor", "connect", "plan", "verify", "storage", "apply", "home", "stock-home", "airplay", "inputs", "usb-status", "usb", "screenshot", "ui"):
        p = commands.add_parser(name)
        if name in ("home", "verify", "plan"):
            p.add_argument("--launcher", choices=sorted(HOME_LAUNCHERS), default=argparse.SUPPRESS)
    p = commands.add_parser("photos"); p.add_argument("action", choices=("install", "choose", "preview", "apply", "status", "settings", "stop"))
    p = commands.add_parser("shortcuts"); p.add_argument("action", choices=("install", "status", "inputs", "usb"))
    p = commands.add_parser("files-access"); p.add_argument("action", choices=("status", "on", "off"))
    p = commands.add_parser("installer"); p.add_argument("action", choices=("status", "on", "off", "settings"))
    p = commands.add_parser("rollback"); p.add_argument("--journal", required=True)
    p = commands.add_parser("perf"); p.add_argument("label")
    for name in ("download-apps", "install"):
        p = commands.add_parser(name); p.add_argument("apps", nargs="*", metavar="APP")
    p = commands.add_parser("launch"); p.add_argument("app", choices=sorted(set(locks()) | {"launcher", "browser", "youtube", "netflix", "projectivy", "tv", "media"}))
    args = parser.parse_args()
    if args.command == "launchers":
        apps = locks()
        print(json.dumps({name: {"component": component, **apps[name]} for name, component in HOME_LAUNCHERS.items()}, ensure_ascii=False, indent=2))
        return
    if args.command == "download-apps":
        _, profile = selected_configuration(args)
        fetch_apps(args.apps or list(default_apps(argparse.Namespace(profile=profile)))); return
    tv = TV(args)
    if args.command == "connect":
        tv.require_serial()
        if ":" in tv.serial:
            print(tv.adb("connect", tv.serial).decode().strip())
        state = tv.adb("-s", tv.serial, "get-state").decode().strip()
        if state != "device":
            raise RuntimeError("The selected TV is not authorized and online.")
        print("Selected ADB device is online; run doctor to check hardware/build.")
        return
    if args.command in ("doctor", "plan"):
        actual = tv.guard(); print(json.dumps(actual, indent=2))
        if args.command == "plan": print(json.dumps(tv.profile, ensure_ascii=False, indent=2))
    elif args.command == "verify":
        report = verify_configuration(tv)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report["ok"]:
            raise RuntimeError("Configuration drift found; review the report. No changes made.")
    elif args.command == "shortcuts":
        if args.action == "install": install_shortcuts(tv)
        elif args.action == "status": print(json.dumps(shortcut_status(tv), indent=2))
        else:
            tv.guard(); print(tv.launch(SHORTCUT_PACKAGES[args.action]))
    elif args.command == "photos":
        if args.action == "install": install_photos(tv)
        elif args.action == "status": print(json.dumps(photo_status(tv), ensure_ascii=False, indent=2))
        elif args.action == "choose":
            photo_access(tv)
            print(tv.shell("am", "start", "-W", "--activity-clear-top", "-n", PHOTO_PACKAGE + "/.MainActivity"))
        elif args.action == "apply": apply_photo_policy(tv)
        else:
            report = photo_status(tv)
            if args.action == "settings":
                resolved = tv.shell("cmd", "package", "resolve-activity", "--brief", "-a", "android.settings.DREAM_SETTINGS")
                if "/" not in resolved or "No activity found" in resolved:
                    raise RuntimeError("This firmware exposes no standard screensaver settings activity. Use photos choose/preview/apply/status; no settings activity opened.")
                print(tv.shell("am", "start", "-W", "-a", "android.settings.DREAM_SETTINGS"))
            elif args.action == "stop":
                dreams = tv.shell("dumpsys", "dreams")
                if re.search(r"mCurrentDream\s*[=:]\s*null", dreams): print("No active system screensaver; current app left unchanged.")
                elif PHOTO_PACKAGE not in dreams: raise RuntimeError("Another system screensaver is active; nothing interrupted.")
                else: print(tv.shell("input", "keyevent", "KEYCODE_DPAD_CENTER"))
            elif not report.get("app", {}).get("can_preview"): raise RuntimeError("No readable USB photo folder selected.")
            else: print(tv.shell("am", "start", "-W", "-n", PHOTO_PACKAGE + "/.PhotoPreviewActivity"))
    elif args.command == "files-access":
        if args.action == "status": print(json.dumps(files_access_status(tv), indent=2))
        else: configure_files_access(tv, args.action == "on")
    elif args.command == "installer":
        if args.action == "status": print(json.dumps(installer_status(tv), ensure_ascii=False, indent=2))
        elif args.action == "settings": installer_settings(tv)
        else: configure_installer(tv, args.action == "on")
    elif args.command == "storage":
        print(json.dumps(internal_storage_status(tv), ensure_ascii=False, indent=2))
    elif args.command == "usb-status":
        print(json.dumps(portable_storage_status(tv), ensure_ascii=False, indent=2))
    elif args.command == "usb": open_portable_storage(tv)
    elif args.command == "apply": apply_profile(tv)
    elif args.command == "rollback": restore(tv, args.journal)
    elif args.command == "install": install_apps(tv, args.apps)
    elif args.command == "airplay": airplay_config(tv)
    elif args.command == "inputs":
        tv.guard()
        tv.shell("input", "keyevent", "KEYCODE_TV_INPUT")
        tree = tv.ui()
        titles = [n for n in tree.iter("node") if n.get("resource-id") == "com.mediatek.wwtv.tvcenter:id/side_panel_title"]
        if not titles:
            raise RuntimeError("Native input selector was not observed; no channel tuning or scan was requested.")
        print("Native source selector opened:", titles[0].get("text"))
        for node in tree.iter("node"):
            if node.get("resource-id") == "com.mediatek.wwtv.tvcenter:id/title":
                print(node.get("text"))
    elif args.command == "home": home_config(tv)
    elif args.command == "stock-home": home_config(tv, stock_mode=True)
    elif args.command == "perf": performance(tv, args.label)
    elif args.command == "screenshot": print(tv.screenshot())
    elif args.command == "ui":
        for node in tv.ui().iter("node"):
            label = node.get("text") or node.get("content-desc")
            if label or node.get("checkable") == "true":
                print(json.dumps({"label": label, "checked": node.get("checked"), "bounds": node.get("bounds"), "id": node.get("resource-id")}, ensure_ascii=False))
    elif args.command == "launch":
        packages = {"browser": "com.phlox.tvwebbrowser", "youtube": "com.google.android.youtube.tv", "netflix": "com.netflix.ninja", "projectivy": "com.spocky.projengmenu", "tv": "com.mediatek.wwtv.tvcenter", "media": "com.mediatek.wwtv.mediaplayer"}
        package = configured_home(tv)[1].split("/")[0] if args.app == "launcher" else packages.get(args.app) or locks()[args.app]["package"]
        if args.app in ("tv", "media"): tv.guard()
        print(tv.launch(package))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, KeyError) as error:
        print("Error:", error, file=sys.stderr)
        sys.exit(1)
