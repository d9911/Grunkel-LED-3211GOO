#!/usr/bin/env python3
# Copyright (C) 2026 Denis Gutsuliak (d9911.org)
# SPDX-License-Identifier: GPL-3.0-or-later
# License and warranty notice: see LICENSE and NOTICE in the project root.
"""Optional laptop screen control and explicit SSH maintenance; no background access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
from urllib.request import Request, urlopen

from grunkel import TV, DEFAULT_PROFILE, ROOT

REMOTE_COMMANDS = {'doctor', 'plan', 'verify', 'storage', 'usb-status', 'screenshot', 'ui',
                   'apply', 'home', 'stock-home', 'airplay', 'inputs', 'usb', 'photos',
                   'installer', 'rollback', 'launch', 'download-apps', 'install'}
SCREEN_OPTIONS = ['--no-audio', '--max-size=1280', '--max-fps=15', '--video-bit-rate=2M',
                  '--no-clipboard-autosync', '--no-power-on', '--shortcut-mod=lalt',
                  '--window-title=Grunkel TV']


def tool_pin():
    lock = json.loads((ROOT / 'remote-tools.lock.json').read_text())
    arch = {'arm64': 'aarch64', 'aarch64': 'aarch64', 'x86_64': 'x86_64'}.get(platform.machine())
    if platform.system() != 'Darwin' or arch not in lock['macos']:
        raise RuntimeError('Automatic bootstrap supports macOS arm64/x86_64 only. Install official scrcpy manually and set SCRCPY.')
    return lock['macos'][arch]


def bootstrap_screen():
    pin = tool_pin()
    destination = ROOT / 'tools' / pin['directory']
    if destination.exists():
        if not (destination / 'scrcpy').is_file():
            raise RuntimeError('Incomplete existing scrcpy directory; inspect it manually. No files overwritten.')
        subprocess.run([str(destination / 'scrcpy'), '--version'], check=True)
        return
    archive = ROOT / 'downloads' / pin['archive']
    archive.parent.mkdir(exist_ok=True)
    if not archive.exists():
        request = Request(pin['url'], headers={'User-Agent': 'Grunkel-TV-maintenance'})
        with urlopen(request, timeout=60) as stream:
            data = stream.read()
        if hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise RuntimeError('Official scrcpy archive SHA-256 mismatch; nothing extracted.')
        with archive.open('xb') as output:
            output.write(data)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != pin['sha256']:
        raise RuntimeError('Existing scrcpy archive SHA-256 mismatch; nothing extracted.')
    tools = ROOT / 'tools'; tools.mkdir(exist_ok=True)
    with tarfile.open(archive) as package:
        for item in package.getmembers():
            parts = Path(item.name).parts
            target = (tools / item.name).resolve()
            if (not parts or parts[0] != pin['directory'] or '..' in parts
                    or not target.is_relative_to(tools.resolve())
                    or not (item.isfile() or item.isdir())):
                raise RuntimeError('Unsafe scrcpy archive entry; nothing extracted.')
        # Every entry was checked; official archives contain only regular files/directories.
        package.extractall(tools)
    subprocess.run([str(destination / 'scrcpy'), '--version'], check=True)


def screen_plan(args):
    tv = TV(argparse.Namespace(profile=str(DEFAULT_PROFILE), serial=args.serial))
    tv.require_serial()
    bundled = None
    try:
        bundled = ROOT / 'tools' / tool_pin()['directory'] / 'scrcpy'
    except RuntimeError:
        pass
    binary = os.environ.get('SCRCPY') or (str(bundled) if bundled and bundled.is_file() else shutil.which('scrcpy'))
    command = [binary or 'scrcpy', '--serial', tv.serial, *SCREEN_OPTIONS,
               '--keyboard=' + ('uhid' if args.hid else 'sdk'),
               '--mouse=' + ('uhid' if args.hid else 'sdk')]
    return tv, command, bool(binary)


def ssh_plan(config_path, arguments):
    config = json.loads(Path(config_path).read_text())
    if not isinstance(config, dict):
        raise ValueError('Remote configuration must be a JSON object.')
    host, directory, serial = (config[k] for k in ('ssh_host', 'project_directory', 'adb_serial'))
    if not isinstance(host, str) or not re.fullmatch(r'(?:[A-Za-z0-9_][A-Za-z0-9_.-]*@)?[A-Za-z0-9][A-Za-z0-9_.-]*', host):
        raise ValueError('Use an SSH config alias or user@hostname; no options or shell commands.')
    if not isinstance(directory, str) or not directory.startswith('/') or any(c in directory for c in '\n\r\0'):
        raise ValueError('Use an absolute POSIX project_directory on the laptop beside the TV.')
    if not isinstance(serial, str) or not re.fullmatch(r'[A-Za-z0-9_.:\[\]%-]+', serial):
        raise ValueError('Use the exact remote ADB serial from adb devices -l.')
    python = config.get('python', 'python3')
    if not isinstance(python, str) or not (python == 'python3' or python.startswith('/')) or any(c in python for c in '\n\r\0'):
        raise ValueError('python must be python3 or an absolute executable path.')
    port = config.get('ssh_port', 22)
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('ssh_port must be an integer from 1 to 65535.')
    if arguments[:1] == ['--']:
        arguments = arguments[1:]
    arguments = arguments or ['doctor']
    if arguments[0] not in REMOTE_COMMANDS or any(a in ('--serial', '--profile') or a.startswith(('--serial=', '--profile=')) for a in arguments):
        raise ValueError('Only documented toolkit commands are allowed; device/profile overrides and raw shell/flash commands are refused.')
    base = [python, 'scripts/grunkel.py', '--serial', serial]
    guard = shlex.join(base + ['doctor'])
    operation = shlex.join(base + arguments)
    remote = 'cd ' + shlex.quote(directory) + ' && '
    remote += 'exec ' + guard if arguments == ['doctor'] else guard + ' && exec ' + operation
    command = ['ssh', '-T', '-a', '-o', 'ForwardX11=no', '-o', 'ClearAllForwardings=yes',
               '-o', 'StrictHostKeyChecking=yes', '-o', 'BatchMode=yes',
               '-o', 'ControlMaster=no', '-o', 'ControlPath=none',
               '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=30',
               '-o', 'ServerAliveCountMax=3', '-p', str(port), host, remote]
    return command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('bootstrap-screen', help='Download/check optional official scrcpy locally; no TV/SSH connection')
    for name in ('screen-plan', 'screen'):
        p = commands.add_parser(name); p.add_argument('--serial')
        mode = p.add_mutually_exclusive_group()
        mode.add_argument('--hid', dest='hid', action='store_true', help='Virtual HID keyboard/mouse (default, checked on this TV)')
        mode.add_argument('--sdk', dest='hid', action='store_false', help='Alternative SDK input; control failed on this TV')
        p.set_defaults(hid=True)
    for name in ('plan', 'run'):
        p = commands.add_parser(name); p.add_argument('--config', default=os.environ.get('GRUNKEL_REMOTE_CONFIG') or str(ROOT / 'remote.local.json'))
        p.add_argument('command', nargs=argparse.REMAINDER, help='-- doctor|verify|storage|...')
    args = parser.parse_args()
    if args.action == 'bootstrap-screen':
        bootstrap_screen(); return
    if args.action in ('screen-plan', 'screen'):
        tv, command, available = screen_plan(args)
        if args.action == 'screen-plan':
            print(json.dumps({'command': command, 'scrcpy_found': available, 'connects_to_tv': False, 'audio_forwarding': False, 'background_service': False}, indent=2)); return
        if not available:
            raise RuntimeError('scrcpy missing. Run make screen-bootstrap, or install official scrcpy and set SCRCPY.')
        tv.guard()
        env = os.environ.copy(); env['ADB'] = tv.binary
        raise SystemExit(subprocess.run(command, env=env).returncode)
    command = ssh_plan(args.config, args.command)
    if args.action == 'plan':
        print(json.dumps({'command': command, 'connects': False, 'note': 'Private host/serial/path; do not publish this output.'}, indent=2)); return
    if not shutil.which('ssh'):
        raise RuntimeError('OpenSSH client is missing.')
    raise SystemExit(subprocess.run(command).returncode)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        print('Error:', error, file=sys.stderr); sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
