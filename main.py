
import os
import subprocess
from datetime import datetime


INPUT_FOLDER = "/Volumes/abcd/ai video automation data/input"
OUTPUT_FOLDER = "/Volumes/abcd/ai video automation data/output"
PROCESSED_FOLDER = "/Volumes/abcd/ai video automation data/processed"
FAILED_FOLDER = "/Volumes/abcd/ai video automation data/failed"
LOG_FOLDER = "/Volumes/abcd/ai video automation data/logs"

os.makedirs(LOG_FOLDER, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_FOLDER,
    f"process_{datetime.now().strftime('%Y-%m-%d')}.log"
)

CLIP_DURATION = 60

FFMPEG = "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
FFPROBE = "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"


os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(FAILED_FOLDER, exist_ok=True)


video_count = 0
success_count = 0
failed_count = 0


def validate_output(output_file):
    """Check whether the generated video is valid."""

    if not os.path.exists(output_file):
        return False, "Output file does not exist"

    if os.path.getsize(output_file) == 0:
        return False, "Output file is empty"

    probe_command = [
        FFPROBE,
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type,width,height:format=duration",
        "-of",
        "default=noprint_wrappers=1",
        output_file
    ]

    try:
        result = subprocess.run(
            probe_command,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return False, "FFprobe could not read the output"

        metadata = result.stdout.strip().splitlines()

        has_video = any("video" in item for item in metadata)
        has_audio = any("audio" in item for item in metadata)

        if not has_video:
            return False, "No video stream found"

        if not has_audio:
            return False, "No audio stream found"

        duration_found = False
        resolution_found = False

        for item in metadata:

            if item.startswith("duration="):
                duration = float(item.split("=")[1])
                if duration > 0:
                    duration_found = True

            if item.startswith("width=") or item.startswith("height="):
                resolution_found = True


        if not duration_found:
            return False, "Invalid video duration"

        if not resolution_found:
            return False, "Invalid video resolution"

        return True, "Valid video, audio, duration and resolution"

    except Exception as error:
        return False, f"Validation error: {error}"

def write_log(message):

    timestamp = datetime.now().strftime("%H:%M:%S")

    with open(LOG_FILE, "a") as log:

        log.write(
            f"[{timestamp}] {message}\n"
        )


for file in os.listdir(INPUT_FOLDER):

    # Ignore Mac hidden files
    if file.startswith("._"):
        continue

    # Only process supported video files
    if not file.lower().endswith((".mp4", ".mkv", ".mov")):
        continue

    video_count += 1

    input_file = os.path.join(INPUT_FOLDER, file)
    name = os.path.splitext(file)[0]

    print("\n" + "=" * 50)
    print(f"Processing: {file}")
    write_log(f"Processing started: {file}")
    print("=" * 50)

    # Get video duration
    duration_cmd = [
        FFPROBE,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        input_file
    ]

    try:
        duration = float(
            subprocess.check_output(duration_cmd)
        )
    except Exception as error:
        print(f"FAILED: Could not read video duration: {error}")

        failed_count += 1

        os.rename(
            input_file,
            os.path.join(FAILED_FOLDER, file)
        )

        continue

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    # Calculate number of clips
    total_parts = int(
        (duration + CLIP_DURATION - 1) // CLIP_DURATION
    )

    print(f"Duration: {minutes:02d}:{seconds:02d}")
    print(f"Total parts: {total_parts}")
    print()
    write_log(
        f"{file} duration: {duration:.2f}s, parts: {total_parts}"
    )

    success = True
    completed_parts = 0

    for part in range(1, total_parts + 1):

        start_time = (part - 1) * CLIP_DURATION

        output_file = os.path.join(
            OUTPUT_FOLDER,
            f"{name}_PART_{part}.mp4"
        )

        # -------------------------------------------------
        # TASK 5: Smart resume - check existing output before processing
        # -------------------------------------------------

        if os.path.exists(output_file):

            valid, message = validate_output(output_file)

            if valid:

                completed_parts += 1

                print(
                    f"[{part}/{total_parts}] "
                    f"✓ Already exists — {message}"
                )
                write_log(
                    f"{file} duration: {duration:.2f}s, parts: {total_parts}"
                )
                continue

            else:

                print(
                    f"[{part}/{total_parts}] "
                    f"Existing file invalid — regenerating"
                )

        # -------------------------------------------------
        # Create the clip
        # -------------------------------------------------

        print(
            f"[{part}/{total_parts}] "
            f"Creating PART {part}..."
        )

        command = [
            FFMPEG,

            "-ss",
            str(start_time),

            "-i",
            input_file,

            "-t",
            str(CLIP_DURATION),

            "-vf",
            (
                "scale=1080:608,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
                f"drawtext=text='PART {part}':"
                "fontcolor=white:"
                "fontsize=80:"
                "box=1:"
                "boxcolor=black@0.7:"
                "boxborderw=20:"
                "x=(w-text_w)/2:"
                "y=250"
            ),

            "-c:v",
            "libx264",

            "-c:a",
            "aac",

            "-y",
            output_file
        ]

        # -------------------------------------------------
        # Run FFmpeg with automatic retries
        # -------------------------------------------------

        max_attempts = 3
        clip_success = False

        progress = int((part / total_parts) * 100)

        print(
            f"\n[Clip {part}/{total_parts} | {progress}%] Starting..."
        )

        for attempt in range(1, max_attempts + 1):

            print(
                f"[Clip {part}/{total_parts}] "
                f"Attempt {attempt}/{max_attempts}"
            )

            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:

                print(
                    f"[{part}/{total_parts}] "
                    f"✗ FFmpeg failed on attempt {attempt}"
                )

                if result.stderr.strip():
                    print(result.stderr.strip())

                if attempt < max_attempts:
                    print("Retrying...")
                    continue

                print("All FFmpeg attempts failed.")
                break

            # -------------------------------------------------
            # Validate newly created clip
            # -------------------------------------------------

            valid, message = validate_output(output_file)

            if not valid:

                print(
                    f"[{part}/{total_parts}] "
                    f"✗ Validation failed on attempt {attempt}: "
                    f"{message}"
                )

                if attempt < max_attempts:
                    print("Retrying...")
                    continue

                print("All attempts failed validation.")
                break

            clip_success = True

            print(
                f"[Clip {part}/{total_parts}] "
                f"✓ Completed — {message}"
            )
            write_log(
                f"{file} PART {part} completed"
            )

            break

        if not clip_success:

            success = False
            continue

        completed_parts += 1

        print(
            f"[{part}/{total_parts}] "
            f"✓ Complete — {message}"
        )

    # -----------------------------------------------------
    # Move original only when ALL clips succeeded
    # -----------------------------------------------------

    if success and completed_parts == total_parts:

        success_count += 1

        print()
        print(f"SUCCESS: {file}")
        write_log(
            f"SUCCESS: {file} completed"
        )
        print(f"Created/verified {completed_parts} clips")

        os.rename(
            input_file,
            os.path.join(PROCESSED_FOLDER, file)
        )

        print("Original moved to processed")

    else:

        failed_count += 1

        print()
        print(f"FAILED: {file}")
        write_log(
            f"FAILED: {file}"
        )

        # -------------------------------------------------
        # Remove partial output clips
        # -------------------------------------------------

        print("Cleaning up partial output clips...")

        for part in range(1, total_parts + 1):

            output_file = os.path.join(
                OUTPUT_FOLDER,
                f"{name}_PART_{part}.mp4"
            )

            if os.path.exists(output_file):

                os.remove(output_file)

                print(
                    f"Removed: {os.path.basename(output_file)}"
                )

        # -------------------------------------------------
        # Move original to failed folder
        # -------------------------------------------------

        os.rename(
            input_file,
            os.path.join(FAILED_FOLDER, file)
        )

        print("Original moved to failed")

print("\n" + "=" * 50)
print("PROCESSING SUMMARY")
print("=" * 50)
print(f"Videos found: {video_count}")
print(f"Successful:   {success_count}")
print(f"Failed:       {failed_count}")
print("=" * 50)
print("All videos completed.")
