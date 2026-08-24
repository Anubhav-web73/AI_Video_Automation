from faster_whisper import WhisperModel


MODEL = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return (
        f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"
    )


def generate_subtitle(video_file, output_srt):

    print(f"Generating subtitles: {video_file}")

    segments, info = MODEL.transcribe(
        video_file,
        language="hi",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False
    )

    print(f"Detected language: {info.language}")

    with open(
        output_srt,
        "w",
        encoding="utf-8"
    ) as srt:

        for index, segment in enumerate(
            segments,
            start=1
        ):

            srt.write(f"{index}\n")

            srt.write(
                f"{format_time(segment.start)} --> "
                f"{format_time(segment.end)}\n"
            )

            srt.write(
                f"{segment.text.strip()}\n\n"
            )

    print(
        f"Subtitle created: {output_srt}"
    )
