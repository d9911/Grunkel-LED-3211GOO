# Grunkel LED-3211GOO — current handoff

Read this file, the chosen-language README and verification.json before touching a TV.
This is toolkit 1.0.0 for one tested unit, not flashable firmware. README.md / README.es.md / README.ru.md contain equivalent user workflows. Full command notes: docs/technical-reference.md. Contribution/release boundaries: CONTRIBUTING.md.

## Current baseline

- Hardware: Expressluck / martin / MediaTek mt5867, Android 14 / API 34, 32-bit armeabi-v7a userspace. Exact fingerprint: profiles/martin-mt5867-android14.json. Never bypass the board/build guard.
- HOME: Couchy 1.0.6, own internal satin-teal-copper JPEG, Dock, XS icons. Eight visible cards: Netflix, AirPlay, Live TV, OpenTV, SmartTube F-Droid, TV Bro, HDMI, USB. Date/24h clock and existing timezone retained. Android/Couchy currently Spanish. RU guide uses neutral European-time wording.
- Alternatives: Projectivy 4.72 has checked RU/ES/EN settings, but custom wallpaper/themes opened Premium. Plume 1.3 has checked free JPEG + Light/Dark/Auto, English-only settings. No purchase or license bypass.
- Couchy RU/ES/EN settings checked. Explicit English is absent from its picker; native app locale and imported language=en worked. System default after language trials left a stale Russian date/UI; explicit Español corrected it. Do not assume all translations or Couchy light/dark were tested.
- Base set is exactly one selected launcher + SmartTube/OpenTV/AirPlay/TV Bro. Factory Netflix/Live TV/YouTube remain. Do not silently install all three launchers.
- Optional own apps: org.d9911.grunkel.photos 0.2.0, org.d9911.grunkel.inputs and org.d9911.grunkel.usb 0.1.0. Sources under android/. These versions are independent of toolkit 1.0.0.

## Read before mutation

1. Use only the owner's exact authorized ADB serial through --serial, GRUNKEL_TV_SERIAL / Make TV, or ignored device.local.json. No network scan or reused addressing from another unit. Run doctor/plan. Tests during preparation must use fixtures, not the owner's device.
2. No autonomous Git changes: preserve the existing staged index. No add/commit/branch/tag, remote mutation, push/PR/release. Owner handles Git manually. A task to finish/validate/release does not authorize publication.
3. Never root/unlock/reset/reboot, clear app data, uninstall apps/updates, write partitions or flash arbitrary images as routine optimization. Owner authorized cache cleanup only. Preserve Netflix, DRM, Google Cast/Play services, WebView, permission/TV/input services and updates.
4. No USB delete/rename/format or modification of existing files. Earlier consent for adding isolated fixtures was a specific test, not a standing cleanup permission. No copy of owner photos into public assets. Keep parental PIN/arrow sequences private; never request/store them.
5. Volume cap is 1/100. Mute before playback/source tests; never assume one Android volume step equals one percent. Silent navigation tests do not prove picture/audio reception.
6. Check live foreground before input. Pause if owner casting/remote changes it. Couchy HOME events preserve open settings: BACK closes subpage and main settings. Use fresh UI/focus; do not send long blind key sequences. MediaTek accessibility XML can be stale: use screenshot + foreground. Black fullscreen captures did not prove a protected-surface cause or successful on-TV media playback.

## USB, HDMI and photos

- HDMI card reads actual TvInputManager entries HDMI1/HW5, HDMI2/HW6, HDMI3/HW7, AV/HW2. Typed channel VIEW intent launches factory TV. HDMI1 active session verified; fresh external pictures/other selections unverified. OEM VIEW_INPUTS launched an unusable panel and is not used by the helper. No key injection, tuning/scan or privileged permission.
- USB card always remains on Couchy HOME. Only controls inside its page turn grey when absent. Reads mounted/mounted_ro removable storage; opens native browser/Photos. No file permissions, network, background service or USB writes in shortcuts.
- Physical owner remove/reinsert verified automatic controls off/on and previous photo folder availability. USB/SD distinction is not guaranteed by generic public-volume CLI output.
- Photos: idle 300000ms (5min), interval 30000ms, sleep total 1800000ms (30min) = 25min photos. Selected private folder must survive testing. Arrow/OK/BACK folder navigation; preview left/right, OK pause, BACK exit; max 1000 candidates, decode 1280x720. JPEG/PNG and corrupt-skip loop checked.
- Never shorten sleep for another routine test: an earlier test disconnected ADB and needed the owner to wake TV. Full current 30min cycle and reboot/reset retention remain unverified. Active playback/HDMI may hold awake. Manual preview is separate and holds awake. No root-only dreams commands.

## Commands, consent and recovery

- make check is offline only. make verify reads selected five APKs/profile/HOME/photos; not PIN, all translations, actual media picture or reset survival. make storage is read-only. Review drift before apply; OEM FAST app/error-report values reverted before, cause unknown.
- New TV: make install LAUNCHER=name; make menu LAUNCHER=name, finish welcome; make configure LAUNCHER=name. No private card layout, playlist, PIN or folder is auto-imported. make setup is for welcome-completed TVs. Sequence/failure-stop is enforced even with -j.
- make launcher-install installs only one launcher without HOME change; launcher-use explicitly assigns HOME and saves per-serial/fingerprint selection privately. Priority: --launcher > env/Make > launcher.local.json > profile Couchy. Exact old HOME/local entry/file absence is journaled. stock-home retains selection. Inactive alternatives need not be installed/enabled; apply must never disable a known launcher through a custom optional list.
- Supported settings/app-ops preserve exact previous values in private journals; restore only on the same hardware/serial, reverse order. Installation journals/backups do not imply automatic uninstall or full app-data recovery.
- Optional Material Files 1.7.5 is needed for this OEM's stub document picker. Owner explicitly allowed shared TV/attached-drive storage; current MANAGE_EXTERNAL_STORAGE allow, original default journaled. It permits writes/deletes too. No laptop shares connected. Do not extend that consent to a different owner. files-access status/on/off is separate from setup and from APK installation permission.
- REQUEST_INSTALL_PACKAGES is deny for installed Projectivy/Plume/TV Bro/Material Files. installer on allows only Projectivy if present; off closes all reviewed sources. No automatic timeout, no extra app store, system installer/ADB retained.
- Couchy native Save/Load JSON and JPEG picker worked. Keep native JSON private (full package inventory); wallpaper original must be backed up separately. Use Material Files once; don't alter persistent resolver defaults. Plume private data is inaccessible via ordinary ADB; reserves are not firmware or full private app-data images.
- Preserve tools/photo-signing and tools/shortcut-signing privately for signed updates. Builders pin official JDK/SDK archives and permit compatible manual --toolchain. APKs/keys/pointers stay under ignored tools/downloads; install verifies local build and on-device hashes.
- Optional scrcpy 5.0.1 defaults to UHID, audio/clipboard sync off, no stay-awake/power-on service. Owner confirmed picture and HID mouse/keyboard; SDK input failed. Cross-site SSH/desktop and physical USB/Bluetooth peripherals untested. RustDesk was documentation only, not installed. No public ADB port or unattended credentials.

## Evidence and public boundary

verification.json is a compact current evidence index; hardware.json keeps sources/calculations. Preserve uncertainty: no zero-telemetry/permanent-speedup/universal-ROM claim. Vendor ACR was running. Current Spanish is not a factory-reset default. Cast is retained; owner confirmed iPhone mirroring and Redmi YouTube casting, not full Android mirroring or Netflix playback.

Public pixels are exactly current Couchy HOME + preserved historical home-es.png + original JPEG; hashes/provenance in assets/showcase.json and scripts/export-public.py must match. Do not relabel old Projectivy as Couchy or export owner media. All raw screenshots/logs, APKs, keys, addressing, local choice files and backups stay ignored. The exporter is the authoritative whitelist. Prior notes/images were retained privately before stable cleanup; do not restore superseded historical state into current instructions. Do not create memory entries outside this project unless explicitly asked.
