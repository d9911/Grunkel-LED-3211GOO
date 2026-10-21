# Technical reference — toolkit 1.0.0

User workflows: [English](../README.md), [Español](../README.es.md), [Русский](../README.ru.md). Current state: [AGENTS.md](../AGENTS.md), [verification.json](../verification.json). These advanced commands use the same guarded toolkit; they do not flash firmware.

## Device selection and platform support

From the project root, copy device.example.json to ignored device.local.json and replace its adb_address placeholder. TV=EXACT_SERIAL overrides the local file. LAN connect uses only that address; a USB serial is checked directly. USB debugging alone is not proof that a TV socket supports a PC data cable. Never expose ADB through a router.

Python 3.9+ and GNU Make are required for wrappers. Official ADB is bootstrapped for supported hosts; only macOS was exercised. Own Java builders automatically bootstrap pinned macOS arm64 JDK/Android tools. On another host prepare a compatible layout and run `python3 scripts/build-photos.py --toolchain DIRECTORY` / `python3 scripts/build-shortcuts.py --toolchain DIRECTORY`; automatic cross-platform Java builds are not established.

## Launcher-only and base variants

```sh
make launcher-list
make launcher-install TV=EXACT_SERIAL LAUNCHER=couchy
make menu TV=EXACT_SERIAL LAUNCHER=couchy
# Finish welcome, then explicitly select HOME:
make launcher-use TV=EXACT_SERIAL LAUNCHER=couchy
make verify TV=EXACT_SERIAL
```

Names: couchy, projectivy, plume. This installs only the named launcher. A complete base variant uses `make install ... LAUNCHER=NAME`, welcome, then `make configure ... LAUNCHER=NAME`; five third-party apps total. Never execute all three alternatives as one setup.

CLI equivalents (launcher override precedes the subcommand):

```sh
python3 scripts/grunkel.py --serial EXACT_SERIAL --launcher couchy download-apps
python3 scripts/grunkel.py --serial EXACT_SERIAL --launcher couchy install
python3 scripts/grunkel.py --serial EXACT_SERIAL --launcher couchy launch launcher
python3 scripts/grunkel.py --serial EXACT_SERIAL home --launcher couchy
```

Couchy export/import is manual native UI, not private file injection. Save configuration writes Download/CouchyBackup.json. Pull it privately, preserve every field and change only `language` to `en` for an English preset, then import through Load configuration. Do not publish package inventories or import another owner's hidden-app list blindly. Russian/Spanish have explicit native picker entries; English does not in 1.0.6. System-default language switching showed a stale date/UI; explicit Español corrected the observed state.

## Couchy picker and wallpaper

```sh
python3 scripts/grunkel.py --serial EXACT_SERIAL download-apps files
python3 scripts/grunkel.py --serial EXACT_SERIAL install files
make files-access-status TV=EXACT_SERIAL
# Only with this owner's permission for shared TV/attached storage:
make files-access-on TV=EXACT_SERIAL
make installer-off TV=EXACT_SERIAL
```

Copy img/satin-teal-copper.jpg into a fresh internal Download folder using your authorized ADB connection, without overwriting owner files. Couchy Settings → Wallpaper → photo → Material Files → JPEG; choose the resolver only once. Couchy copies the photo internally, independent of USB. Use static JPEG, no video/aerial wallpaper. Plume uses its internal wallpaper picker; Projectivy custom photos/themes opened Premium.

All-files access permits modification/deletion as well as reading. No laptop shares are configured. `make files-access-off` denies access; the journal restores the exact original app-op mode, including default. Installed JPEG remains in Couchy's private storage. The picker is optional and outside the five base apps.

## USB photo workflow and cards

```sh
make shortcuts-install TV=EXACT_SERIAL
make shortcuts-inputs TV=EXACT_SERIAL
make shortcuts-usb TV=EXACT_SERIAL
make photos-install TV=EXACT_SERIAL
make photos-choose TV=EXACT_SERIAL
make photos-preview TV=EXACT_SERIAL
make photos-apply TV=EXACT_SERIAL
make photos-status TV=EXACT_SERIAL
make photos-stop TV=EXACT_SERIAL
```

The native DREAM_SETTINGS screen is absent on the tested firmware; photos-settings refuses rather than invoking root-only dreams controls. Do not shorten timers to re-test sleep. The current 5min idle / 25min photos / total30min settings and 30s image interval are configuration, not proof of a full completed cycle. Preserve the selected private folder through all tests.

HDMI helper queries [TvInputManager](https://developer.android.com/reference/android/media/tv/TvInputManager), uses a [pass-through URI](https://developer.android.com/reference/android/media/tv/TvContract) and typed ACTION_VIEW to factory TV. It has no privileged key injection or channel scan. Android connected/standby labels do not prove video reception. Generic public volumes can be USB or SD.

## Optional manual APK installation

```sh
make installer-status TV=EXACT_SERIAL
make installer-settings TV=EXACT_SERIAL
make installer-on TV=EXACT_SERIAL
# In installed Projectivy: Install third-party apps; install a trusted APK.
make installer-off TV=EXACT_SERIAL
```

Only Projectivy is allowed by on; it must already exist. Plume/browser/Material Files remain denied. There is no automatic timeout. Do not disable the system installer or confuse storage access with installation permission.

## Laptop display and controls

```sh
make screen-bootstrap
make screen-plan TV=EXACT_SERIAL
make screen TV=EXACT_SERIAL
# Explicit legacy SDK alternative; it failed the owner trial:
python3 scripts/remote.py screen --sdk
```

scrcpy defaults to UHID keyboard/mouse, 1280px/15fps/2M video, no audio or clipboard autosync, no stay-awake/power-on service. Owner confirmed HID input; left Alt releases mouse capture. No persistent remote service is installed on the TV.

Physical USB mouse/keyboard or a combined USB receiver uses an available TV USB host port; keep media attached through a suitable powered hub if needed. Never connect two USB hosts with an arbitrary A–A cable. Pair Bluetooth peripherals only if offered by the TV settings. Physical USB/Bluetooth input has not been tested; the laptop HID result does not establish it.

## Cross-site maintenance

Prepare an authorized nearby laptop with this toolkit, exact serial and ADB key. Optional laptop-side remote desktop (for example [RustDesk](https://rustdesk.com/)) is manual; no agent, unattended password or credentials are installed by this project. An offline/unprepared laptop cannot be controlled by the toolkit.

Copy remote.example.json to ignored remote.local.json; set the trusted SSH host, absolute project directory and exact ADB serial. Configure SSH known-host/key authentication separately; never forward public ADB.

```sh
make remote-plan
make remote-doctor
make remote-verify
make remote-storage
python3 scripts/remote.py run -- photos status
python3 scripts/remote.py run -- home --launcher couchy
```

The wrapper guards hardware before a whitelisted command; unknown commands/raw shell/flash are refused. Remote output/downloads/journals stay on that laptop. Cross-site SSH/desktop has not been tested. This supports application/configuration maintenance, not reflashing a laptop OS or TV partitions.

## Recovery boundaries

Journals are same-device exact-original-value records, applied in reverse order. HOME selection and package/settings profiles have distinct journals. No implicit uninstall/data clear. Couchy JSON plus JPEG is not a complete app-data or firmware image; Plume private preferences are not available through ordinary ADB. Keep tools/photo-signing and tools/shortcut-signing private for future signed updates.

Full factory-reset/reboot retention, a default Spanish language after reset, all HDMI/AV pictures and Netflix playback remain unverified. Read verification.json before making stronger claims.
