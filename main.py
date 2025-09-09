import argparse
import subprocess
import win32api
import os
import sys
import time

from utils import system_call, magnitude_fmt_time
 
parser = argparse.ArgumentParser(description="Blu-ray 3d repacker",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-d", "--drive", help="address to blu-ray drive", required=True)
parser.add_argument("-crf", "--crf", default="17", help="CRF quality of movie/CQ if hardware acceleration enabled")
parser.add_argument("-t", "--threads", default="16", help="number of threads for ffmpeg")
parser.add_argument("-su", "--skip-unpack", help="skip unpack of eac3to", action=argparse.BooleanOptionalAction)
parser.add_argument("-rac", "--reencode-audio-channel", help="re-encode audio channel", action=argparse.BooleanOptionalAction)
parser.add_argument("-uhac", "--use-hardware-acceleration", help="enabling nvidia cuda & nvenc", action=argparse.BooleanOptionalAction)
args = parser.parse_args()
config = vars(args)

start_time = time.perf_counter_ns() # bench start
[eac3to_info, eac3_success] = system_call(
    ["./eac3to/eac3to.exe", config['drive'], "1)"], 
)
if not eac3_success:
    print("Something happend with eac3to, can't gather drive info")
    exit(1)

info_tracks = {}
for line in eac3to_info.split("\n"):
    line_data = line.replace("\x08", "").strip().split(": ")
    if len(line_data) < 2:
        continue
    
    info_types = line_data[1].split(", ")
    info_tracks[line_data[0]] = info_types

audio_track_ac3 = None
audio_track_dts = None
left_eye_track = None
right_eye_track = None
# subtitle_track = None

volume_info = win32api.GetVolumeInformation(f"{config['drive']}\\")
volume_escaped = volume_info[0].replace(" ", "_")

SCRIPT_FOLDER = os.path.dirname(os.path.abspath(sys.argv[0]))
FOLDER_NAME = f"{SCRIPT_FOLDER}\\outputs\\{volume_escaped}"
TEMP_FOLDER_NAME = f"{SCRIPT_FOLDER}\\temp\\{volume_escaped}"
try:
    os.makedirs(FOLDER_NAME)
    print("output folder created")
except:
    print("output folder exist")
try:
    os.makedirs(TEMP_FOLDER_NAME)
    print("temp folder created")
except:
    print("temp folder exist")

for index, track in info_tracks.items():
    if track[0].startswith("h264"):
        # video tracks
        if track[0].endswith("(left eye)"):
            # video track for left eye
            left_eye_track = f"{index}:{TEMP_FOLDER_NAME}\\left.h264"
        if track[0].endswith("(right eye)"):
            # video track for right eye
            right_eye_track = f"{index}:{TEMP_FOLDER_NAME}\\right.h264"
        continue
    if track[0].startswith("AC3") and audio_track_ac3 == None:
        # audio tracks (ac3)
        if track[1].startswith("Russian"):
            audio_track_ac3 = f"{index}:{TEMP_FOLDER_NAME}\\audio_ru.ac3"
        continue
    if track[0].startswith("DTS") and audio_track_dts == None:
        # audio tracks (dts)
        if track[1].startswith("Russian"):
            audio_track_dts = f"{index}:{TEMP_FOLDER_NAME}\\audio_ru.dts"
        continue
    if track[0].startswith("Subtitle (PG5)"):
        # subtitles
        # TODO: Burn hard subs
        continue

if not (audio_track_ac3 or audio_track_dts) or not left_eye_track or not right_eye_track:
    print("Some of tracks wasn't found! Please write additional conditions")
    print("Audio Track (AC3)", audio_track_ac3)
    print("Audio Track (DTS)", audio_track_dts)
    print("Video (left)", left_eye_track)
    print("Video (right)", right_eye_track)
    print(eac3to_info)
    exit(1)

if not config['skip_unpack']:
    extract_ps = subprocess.run(["eac3to/eac3to.exe", config['drive'], "1)", (audio_track_ac3 or audio_track_dts), left_eye_track, right_eye_track])
    if extract_ps.returncode != 0:
        print("eac3to can't succesful extract tracks, check log plz!")
        exit(1)

audio_options = [
    "-c:a",
    "aac",
    "-b:a",
    "383k"
] if config['reencode_audio_channel'] else [
    "-c:a",
    "copy"
]

hwaccel_options = [
    "-hwaccel",
    "cuda",
    "-hwaccel_output_format",
    "cuda"
]if config['use_hardware_acceleration'] else []

video_options = [
    "-c:v",
    "h264_nvenc",
    "-preset",
    "medium",
    "-cq",
    config['crf'],
] if config['use_hardware_acceleration'] else [
    "-c:v",
    "libx264",
    "-preset",
    "medium",
    "-crf",
    config['crf'],
]

frim_ps = subprocess.Popen(
    [
        "FRIM\\FRIMDecode64.exe",
        "-i:mvc",
        f"{TEMP_FOLDER_NAME}\\left.h264",
        f"{TEMP_FOLDER_NAME}\\right.h264",
        "-tab",
        "-o",
        "-"
    ],
    shell=True, stdout=subprocess.PIPE
)
process = subprocess.run(
    [
        "ffmpeg",
        "-y",
        *hwaccel_options,
        "-f",
        "rawvideo",
        "-s:v",
        "1920x2160",
        "-r",
        "24000/1001",
        "-thread_queue_size",
        "2048",
        "-i",
        "-",
        "-i",
        f"{TEMP_FOLDER_NAME}\\audio_ru.ac3" if not audio_track_ac3 is None else f"{TEMP_FOLDER_NAME}\\audio_ru.dts",
        "-pix_fmt",
        "yuv420p",
        *video_options,
        *audio_options,
        "-threads",
        config['threads'],
        f"{FOLDER_NAME}\\film.mp4"
    ], 
    stdin=frim_ps.stdout
)
frim_ps.wait()

try:
    os.removedirs(TEMP_FOLDER_NAME)
except:
    print("cant remove temp folder", TEMP_FOLDER_NAME)

print("We're done here! Your movie is waiting in output folder!")

end_time = time.perf_counter_ns()
print(f"Encoding took: {magnitude_fmt_time(end_time - start_time)}, {end_time - start_time}")