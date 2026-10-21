#!/usr/bin/env python3
# Copyright (C) 2026 Denis Gutsuliak (d9911.org)
# SPDX-License-Identifier: GPL-3.0-or-later
# License and warranty notice: see LICENSE and NOTICE in the project root.
"""Generate a small silent USB test pack in a NEW local folder; never copy to a drive."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent.parent


def run(command):
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Media tool failed.")
    return result.stdout


def generate(output):
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("Optional test pack requires ffmpeg and ffprobe on the computer; no TV app is required.")
    # Exclusive mkdir and ffmpeg -n preserve all pre-existing folders and files.
    output.mkdir(parents=True, exist_ok=False)
    prefix = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n"]
    images = (("01-color-bars.png", "png"), ("02-color-bars.jpg", "mjpeg"))
    for filename, codec in images:
        command = prefix + ["-f", "lavfi", "-i", "smptebars=size=1280x720:rate=1",
                            "-frames:v", "1", "-c:v", codec]
        if codec == "mjpeg":
            command += ["-q:v", "2"]
        run(command + ["-an", "-update", "1", str(output / filename)])
    video = "03-motion-silent-720p.mp4"
    run(prefix + ["-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=25",
                  "-t", "6", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                  "-profile:v", "baseline", "-level:v", "3.1", "-pix_fmt", "yuv420p",
                  "-movflags", "+faststart", "-an", str(output / video)])
    probes = {}
    for filename, expected in (*images, (video, "h264")):
        probe = json.loads(run([ffprobe, "-v", "error", "-show_streams", "-show_format",
                                "-of", "json", str(output / filename)]))
        streams = probe.get("streams", [])
        if len(streams) != 1 or streams[0].get("codec_type") != "video":
            raise RuntimeError("Test file must contain exactly one video stream and NO audio: " + filename)
        stream = streams[0]
        if stream.get("codec_name") != expected or (stream.get("width"), stream.get("height")) != (1280, 720):
            raise RuntimeError("Unexpected test media format: " + filename)
        if filename == video and abs(float(probe["format"]["duration"]) - 6) > 0.1:
            raise RuntimeError("Unexpected test video duration.")
        probes[filename] = {"codec": expected, "width": 1280, "height": 720, "audio_streams": 0}
        if filename == video:
            probes[filename].update({"duration_s": 6, "frame_rate": "25/1"})
    readme = """Grunkel portable-media test pack / Prueba USB / Проверка USB

EN: Generated colour bars: PNG and JPEG, 1280x720. MP4: H.264 baseline,
720p25, 6 seconds, NO AUDIO TRACK. Open only these test files in the native
media browser. Do not delete, rename or format other drive content.
Keep the TV muted for testing; never raise volume above the owner's 1/100 cap.
The files test image display and silent video only; they do not test audio.

ES: Barras de color PNG/JPEG, 1280x720. MP4 H.264 baseline, 720p25,
6 segundos, SIN PISTA DE AUDIO. Abre solo estos archivos de prueba.
No borres, renombres ni formatees otros datos. Mantén el televisor silenciado;
no subas el volumen por encima del límite del propietario de 1/100.
Estas pruebas no comprueban el sonido.

RU: Цветовые полосы PNG/JPEG, 1280x720. MP4 H.264 baseline, 720p25,
6 секунд, БЕЗ ЗВУКОВОЙ ДОРОЖКИ. Открывай только эти тестовые файлы.
Другие данные не удалять, не переименовывать, флешку не форматировать.
Тестировать с отключённым звуком; не повышать громкость выше 1/100.
Эти файлы не проверяют воспроизведение звука.

Copyright (C) 2026 Denis Gutsuliak (d9911.org)
Toolkit source license: GPL-3.0-or-later; see project LICENSE and NOTICE.
"""
    with (output / "README.txt").open("x", encoding="utf-8") as f:
        f.write(readme)
    manifest = {"schema": 1, "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "purpose": "Generated non-personal image and silent-video fixtures",
                "contains_audio": False, "tv_volume_changed": False,
                "copied_to_usb": False, "files": {}}
    for filename in (*probes, "README.txt"):
        data = (output / filename).read_bytes()
        manifest["files"][filename] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                        **probes.get(filename, {})}
    with (output / "manifest.json").open("x", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"folder": str(output), "media_files": len(probes),
                      "audio_streams": 0, "copied_to_usb": False}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default = ROOT / "downloads" / ("Grunkel-Test-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
    parser.add_argument("--output", type=Path, default=default, help="NEW local output directory; existing paths are refused")
    args = parser.parse_args()
    generate(args.output.resolve())


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print("Error:", error, file=sys.stderr)
        sys.exit(1)
