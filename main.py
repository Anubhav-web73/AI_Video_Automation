
import os
import subprocess


INPUT_FOLDER = "/Volumes/abcd/ai video automation data/input"
OUTPUT_FOLDER = "/Volumes/abcd/ai video automation data/output"
PROCESSED_FOLDER = "/Volumes/abcd/ai video automation data/processed"
FAILED_FOLDER = "/Volumes/abcd/ai video automation data/failed"

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
        "stream=codec_type",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
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

        streams = result.stdout.strip().splitlines()

        has_video = "video" in streams
        has_audio = "audio" in streams

        if not has_video:
            return False, "No video stream found"

        if not has_audio:
            return False, "No audio stream found"

        return True, "Valid video and audio"

    except Exception as error:
        return False, f"Validation error: {error}"


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

    success = True
    completed_parts = 0

    for part in range(1, total_parts + 1):

        start_time = (part - 1) * CLIP_DURATION

        output_file = os.path.join(
            OUTPUT_FOLDER,
            f"{name}_PART_{part}.mp4"
        )

        # -------------------------------------------------
        # TASK 3: Check existing output before processing
        # -------------------------------------------------

        if os.path.exists(output_file):

            valid, message = validate_output(output_file)

            if valid:

                completed_parts += 1

                print(
                    f"[{part}/{total_parts}] "
                    f"✓ Already exists — {message}"
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

        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL
        )

        if result.returncode != 0:

            print(
                f"[{part}/{total_parts}] "
                f"✗ FFmpeg failed"
            )

            success = False
            continue

        # -------------------------------------------------
        # Validate newly created clip
        # -------------------------------------------------

        valid, message = validate_output(output_file)

        if not valid:

            print(
                f"[{part}/{total_parts}] "
                f"✗ Validation failed: {message}"
            )

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

        os.rename(
            input_file,
            os.path.join(FAILED_FOLDER, file)
        )


print("\n" + "=" * 50)
print("PROCESSING SUMMARY")
print("=" * 50)
print(f"Videos found: {video_count}")
print(f"Successful:   {success_count}")
print(f"Failed:       {failed_count}")
print("=" * 50)
print("All videos completed.")