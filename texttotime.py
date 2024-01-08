from tgt import read_textgrid
import datetime
import os
import pyttsx3
import re

def generate_textgrid(text, output_wav, output_textgrid):
    # Convert text to speech and save as WAV file
    engine = pyttsx3.init()
    engine.save_to_file(text, output_wav)
    engine.runAndWait()

    # Load the generated WAV file
    # You can use other audio processing libraries here
    # For simplicity, let's use pydub
    from pydub import AudioSegment

    audio = AudioSegment.from_wav(output_wav)

    # Create a TextGrid-like structure
    intervals = []
    current_time = 0

    # Split text into segments
    segments = re.findall(r'<s>(.*?)<\/s>', text)

    for segment in segments:
        segment = segment.strip()
        duration = len(segment.split())  # Duration based on the number of words (adjust as needed)
        intervals.append((current_time, current_time + duration, segment))
        current_time += duration

    # Save TextGrid-like information to a file
    with open(output_textgrid, 'w', encoding='utf-8') as textgrid_file:
        textgrid_file.write("File type = \"ooTextFile\"\n")
        textgrid_file.write("Object class = \"TextGrid\"\n\n")
        textgrid_file.write(f"xmin = 0\n")
        textgrid_file.write(f"xmax = {current_time}\n")
        textgrid_file.write(f"tiers? <exists>\n")
        textgrid_file.write(f"size = 1\n")
        textgrid_file.write(f"item []:\n")
        textgrid_file.write(f"    item [1]:\n")
        textgrid_file.write(f"        class = \"IntervalTier\"\n")
        textgrid_file.write(f"        name = \"Text\"\n")
        textgrid_file.write(f"        xmin = 0\n")
        textgrid_file.write(f"        xmax = {current_time}\n")
        textgrid_file.write(f"        intervals: size = {len(intervals)}\n")

        for i, (start, end, segment) in enumerate(intervals, start=1):
            textgrid_file.write(f"        intervals [{i}]:\n")
            textgrid_file.write(f"            xmin = {start}\n")
            textgrid_file.write(f"            xmax = {end}\n")
            textgrid_file.write(f"            text = \"{segment}\"\n")


def convert_to_srt_timecode(seconds):
    td = datetime.timedelta(seconds=int(seconds))
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    microseconds = (seconds - int(seconds)) * 1e6
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{int(microseconds):03d}"

def convert_textgrid_to_srt(input_file_path, output_directory, interval_length=10):
    try:
        tg = read_textgrid(os.path.join(input_file_path))
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        return

    output_file_path = os.path.join(output_directory, 'output.srt')

    # Create the output directory if it does not exist
    os.makedirs(output_directory, exist_ok=True)

    with open(output_file_path, 'w', encoding='utf-8') as f:
        for tier in tg.tiers:
            if tier.name == "phones":
                continue  # Skip the 'phones' tier
            sentence_buffer = []
            start_time = 0
            sequence_number = 1

            for interval in tier.intervals:
                words = interval.text.split()
                if words and words[0] == "[bracketed]":
                    continue  # Skip unwanted sentences
                sentence_buffer.append(interval.text)
                end_time = interval.end_time

                # Check if the buffer contains 2-3 sentences or the time interval is reached
                if len(sentence_buffer) >= 3 or (end_time - start_time) >= interval_length:
                    combined_sentence = ' '.join(sentence_buffer)
                    f.write(f"{sequence_number}\n")
                    f.write(f"{convert_to_srt_timecode(start_time)} --> {convert_to_srt_timecode(min(start_time + interval_length, end_time))}\n")
                    f.write(f"{combined_sentence}\n\n")
                    sentence_buffer = []
                    start_time = end_time
                    sequence_number += 1

            # Write any remaining sentences in the buffer
            if sentence_buffer:
                combined_sentence = ' '.join(sentence_buffer)
                f.write(f"{sequence_number}\n")
                f.write(f"{convert_to_srt_timecode(start_time)} --> {convert_to_srt_timecode(min(start_time + interval_length, end_time))}\n")
                f.write(f"{combined_sentence}\n\n")
                sequence_number += 1

    print(f"Conversion successful. Output saved to {output_file_path}")

# Example usage:
# convert_textgrid_to_srt('your_input_directory', 'your_output_directory', interval_length=2)