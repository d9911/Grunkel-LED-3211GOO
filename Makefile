# Copyright (C) 2026 Denis Gutsuliak (d9911.org)
# SPDX-License-Identifier: GPL-3.0-or-later
# License and warranty notice: see LICENSE and NOTICE.

.DEFAULT_GOAL := help
# TV operations must stay ordered, even when the caller passes -j.
.NOTPARALLEL:

PYTHON ?= python3
TV ?=
JOURNAL ?=
OUTPUT ?=
LAUNCHER ?=
REMOTE_CONFIG ?=

# Pass user values through the environment, never interpolate them as shell code.
ifneq ($(strip $(TV)),)
export GRUNKEL_TV_SERIAL := $(TV)
endif
ifneq ($(strip $(LAUNCHER)),)
export GRUNKEL_LAUNCHER := $(LAUNCHER)
endif
export GRUNKEL_ROLLBACK_JOURNAL := $(JOURNAL)
export GRUNKEL_EXPORT_OUTPUT := $(OUTPUT)
ifneq ($(strip $(REMOTE_CONFIG)),)
export GRUNKEL_REMOTE_CONFIG := $(REMOTE_CONFIG)
endif

.PHONY: check shortcuts-build shortcuts-install shortcuts-status shortcuts-inputs shortcuts-usb files-access-status files-access-on files-access-off launcher-list launcher-install launcher-use screen-bootstrap screen-plan screen screen-hid remote-plan remote-doctor remote-verify remote-storage help bootstrap connect doctor plan storage download install setup configure apply airplay home verify menu browser tv inputs media usb-status usb test-media photos-build photos-install photos-choose photos-preview photos-apply photos-status photos-settings photos-stop installer-status installer-on installer-off installer-settings stock-home rollback export

help:
	@printf '%s\n' \
	  'Grunkel LED-3211GOO - Python + official ADB; no firmware flashing' \
	  '' \
	  'Select one authorized TV: TV=EXACT_USB_SERIAL or TV=TV_ADDRESS:PORT' \
	  'Alternatively use GRUNKEL_TV_SERIAL or private device.local.json.' \
	  '' \
	  'make install       Prepare ADB, connect, check identity, download/install five apps' \
	  'make setup         install + configure; finish selected launcher welcome FIRST' \
	  'make configure     Apply profile, set AirPlay/HOME, verify, open selected menu' \
	  'make menu          Open the selected launcher' \
	  '' \
	  'make check          Offline project/docs/image/privacy validation; no TV/network' \
	  'make launcher-list  List Plume / Projectivy / Couchy pins without a TV connection' \
	  'make launcher-install LAUNCHER=couchy  Install ONLY that launcher; retain HOME' \
	  'make launcher-use LAUNCHER=couchy  Select installed pinned launcher as HOME' \
	  'LAUNCHER=plume|projectivy|couchy also selects the five-app install/setup variant.' \
	  'make bootstrap     Install official local Platform Tools if missing' \
	  'make connect       Connect LAN ADB, or check the exact USB serial' \
	  'make doctor        Read-only hardware/build identity check' \
	  'make plan          Read-only identity and full change profile' \
	  'make verify        Read-only package/settings/HOME/APK verification' \
	  'make storage       Read data capacity, available RAM and firmware mount flags' \
	  'make download      Download/check only the five default APKs' \
	  'make apply         Apply the reversible privacy/settings profile' \
	  'make airplay       Configure the installed AirPlay receiver' \
	  'make home          Select chosen HOME; remember per TV, with rollback' \
	  'make browser|tv|inputs|media  Open the requested TV function' \
	  'make test-media    Generate local PNG/JPEG + silent MP4 fixtures (ffmpeg)' \
	  'make usb-status    Read portable-drive availability without listing files' \
	  'make usb           Open factory media browser only with a readable drive' \
	  'make photos-install  Build/install original offline USB photo app (optional)' \
	  'make photos-choose   Choose a USB photo folder on the TV' \
	  'make photos-preview|photos-apply|photos-status  Preview/apply 5+25min/read status' \
	  'make photos-settings|photos-stop  Settings if supported/stop active photo screensaver' \
	  'make installer-status|installer-settings  Check/open APK-source settings' \
	  'make installer-on  Temporarily allow Projectivy APK requests; browser stays off' \
	  'make installer-off Disable APK requests from Plume, Projectivy, TV Bro and Material Files (default)' \
	  'make files-access-status|files-access-on|files-access-off  Optional picker storage access; explicit grant with rollback' \
	  'make shortcuts-install  Build/install offline HDMI/AV and USB HOME cards' \
	  'make shortcuts-status|shortcuts-inputs|shortcuts-usb  Check/open offline shortcuts' \
	  'make stock-home    Return to factory HOME; retain apps and profile' \
	  'make rollback JOURNAL=backups/FOLDER/changes.json' \
	  'make screen-bootstrap  Prepare optional pinned scrcpy (macOS; no TV changes)' \
	  'make screen-plan|screen|screen-hid  Plan/show/control TV from laptop; audio off' \
	  'make remote-plan|remote-doctor|remote-verify|remote-storage  Explicit SSH maintenance' \
	  'make export OUTPUT=exports/NEW_NAME.zip  Export reviewed public files' \
	  '' \
	  'New TV: make install, finish welcome with make menu, then make configure.' \
	  'Layout, clock, playlists, language and parental code remain manual UI steps.' \
	  'No root, reset, reboot, partition writes, USB file changes or Git operations.'

bootstrap:
	"$(PYTHON)" scripts/bootstrap-adb.py

connect:
	"$(PYTHON)" scripts/grunkel.py connect

doctor plan verify storage apply airplay home stock-home usb-status usb:
	"$(PYTHON)" scripts/grunkel.py $@

download:
	"$(PYTHON)" scripts/grunkel.py download-apps

# Recursive calls intentionally run in order and stop at the first failure.
# No device mutation happens until the identity check has succeeded.
install:
	$(MAKE) bootstrap
	$(MAKE) connect
	$(MAKE) doctor
	$(MAKE) download
	"$(PYTHON)" scripts/grunkel.py install
	@printf '%s\n' 'Five default apps installed/verified. On a new TV, finish selected launcher welcome with make menu before make configure.'

# The welcome screen cannot be completed by package installation alone.
# Existing owner layout and parental-code settings are not reset or overwritten.
setup:
	$(MAKE) install
	$(MAKE) configure

configure:
	$(MAKE) bootstrap
	$(MAKE) connect
	$(MAKE) doctor
	$(MAKE) apply
	$(MAKE) airplay
	$(MAKE) home
	$(MAKE) installer-off
	$(MAKE) verify
	$(MAKE) menu

launcher-list:
	"$(PYTHON)" scripts/grunkel.py launchers

# Selection is passed as one quoted argument; installation does not change HOME.
launcher-install:
	@test -n "$$GRUNKEL_LAUNCHER" || { printf '%s\n' 'Set LAUNCHER=plume, projectivy or couchy.' >&2; exit 2; }
	$(MAKE) bootstrap
	$(MAKE) connect
	$(MAKE) doctor
	"$(PYTHON)" scripts/grunkel.py download-apps "$$GRUNKEL_LAUNCHER"
	"$(PYTHON)" scripts/grunkel.py install "$$GRUNKEL_LAUNCHER"
	$(MAKE) installer-off

launcher-use:
	@test -n "$$GRUNKEL_LAUNCHER" || { printf '%s\n' 'Set LAUNCHER=plume, projectivy or couchy.' >&2; exit 2; }
	$(MAKE) bootstrap
	$(MAKE) connect
	$(MAKE) doctor
	$(MAKE) home
	$(MAKE) installer-off

menu:
	"$(PYTHON)" scripts/grunkel.py launch launcher

browser tv media:
	"$(PYTHON)" scripts/grunkel.py launch $@

inputs:
	"$(PYTHON)" scripts/grunkel.py inputs

rollback:
	@test -n "$$GRUNKEL_ROLLBACK_JOURNAL" || { printf '%s\n' 'Set JOURNAL to the exact private changes.json path.' >&2; exit 2; }
	"$(PYTHON)" scripts/grunkel.py rollback --journal "$$GRUNKEL_ROLLBACK_JOURNAL"

export:
	@test -n "$$GRUNKEL_EXPORT_OUTPUT" || { printf '%s\n' 'Set OUTPUT to a NEW archive filename; previous archives are preserved.' >&2; exit 2; }
	"$(PYTHON)" scripts/export-public.py --output "$$GRUNKEL_EXPORT_OUTPUT"

# Local generation only: this never selects or writes a USB drive.
test-media:
	"$(PYTHON)" scripts/generate-test-media.py

installer-status installer-on installer-off installer-settings:
	"$(PYTHON)" scripts/grunkel.py installer $(patsubst installer-%,%,$@)

photos-build:
	"$(PYTHON)" scripts/build-photos.py --bootstrap

photos-install:
	$(MAKE) bootstrap
	$(MAKE) photos-build
	$(MAKE) connect
	"$(PYTHON)" scripts/grunkel.py photos install

photos-choose photos-preview photos-apply photos-status photos-settings photos-stop:
	"$(PYTHON)" scripts/grunkel.py photos $(patsubst photos-%,%,$@)

# Optional and foreground only; base install/setup do not install remote tools.
screen-bootstrap:
	"$(PYTHON)" scripts/remote.py bootstrap-screen

screen-plan screen:
	"$(PYTHON)" scripts/remote.py $@

screen-hid:
	"$(PYTHON)" scripts/remote.py screen --hid

remote-plan:
	"$(PYTHON)" scripts/remote.py plan -- doctor

remote-doctor remote-verify remote-storage:
	"$(PYTHON)" scripts/remote.py run -- $(patsubst remote-%,%,$@)

# Optional file picker only; does not change the five-app baseline.
files-access-status files-access-on files-access-off:
	"$(PYTHON)" scripts/grunkel.py files-access $(patsubst files-access-%,%,$@)

# Own optional shortcuts: build locally; no change to the five third-party base apps.
shortcuts-build:
	"$(PYTHON)" scripts/build-shortcuts.py --bootstrap

shortcuts-install:
	$(MAKE) bootstrap
	$(MAKE) shortcuts-build
	$(MAKE) connect
	$(MAKE) doctor
	"$(PYTHON)" scripts/grunkel.py shortcuts install

shortcuts-status shortcuts-inputs shortcuts-usb:
	"$(PYTHON)" scripts/grunkel.py shortcuts $(patsubst shortcuts-%,%,$@)

# Read-only source validation; the only output is an automatically removed temporary public ZIP.
check:
	"$(PYTHON)" scripts/check-project.py
