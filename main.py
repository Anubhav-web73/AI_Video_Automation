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


for file in os.listdir(INPUT_FOLDER):

    # ignore Mac hidden files
    if file.startswith("._"):
        continue

    if file.lower().endswith((".mp4", ".mkv", ".mov")):

        input_file = os.path.join(INPUT_FOLDER, file)
        name = os.path.splitext(file)[0]

        print("\n" + "="*50)
        print(f"Processing: {file}")
        print("="*50)


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


        duration = float(subprocess.check_output(duration_cmd))

        total_parts = int(duration // CLIP_DURATION) + 1


        success = True


        for part in range(1, total_parts + 1):

            start_time = (part - 1) * CLIP_DURATION


            output_file = os.path.join(
                OUTPUT_FOLDER,
                f"{name}_PART_{part}.mp4"
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
                    "scale=1080:-1,"
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


            result = subprocess.run(command)


            if result.returncode != 0:
                success = False
                break



        if success:

            print("SUCCESS:", file)

            os.rename(
                input_file,
                os.path.join(PROCESSED_FOLDER,file)
            )

        else:

            print("FAILED:", file)

            os.rename(
                input_file,
                os.path.join(FAILED_FOLDER,file)
            )


print("\nAll videos completed.")