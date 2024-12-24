import ffmpeg
import whisper
import nltk
from nltk.tokenize import word_tokenize
import os
import argparse
from tkinter import filedialog
import tkinter as tk

# Ensure NLTK data is downloaded
nltk.download('punkt')

def select_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(
        title="Select Podcast File",
        filetypes=[
            ("Audio Files", "*.mp3 *.wav *.m4a *.aac"),
            ("All Files", "*.*")
        ]
    )
    return file_path if file_path else None

def convert_audio(input_path, output_path):
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
            .overwrite_output()
            .run(quiet=True)
        )
        print(f"Converted {input_path} to {output_path}")
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e}")
        return False
    return True

def transcribe_audio(audio_path):
    model = whisper.load_model("base")  # You can choose other models like 'small', 'medium', etc.
    print("Transcribing audio...")
    result = model.transcribe(audio_path, word_timestamps=True)
    print("Transcription complete.")
    return result

def find_keywords(transcription, keywords):
    keyword_occurrences = []

    for segment in transcription['segments']:
        for word_info in segment.get('words', []):
            word = word_info['word'].lower()
            for keyword in keywords:
                if keyword.lower() in word:
                    start = word_info['start']  # in seconds
                    keyword_occurrences.append({
                        'keyword': keyword,
                        'time': start
                    })
    return keyword_occurrences

def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hrs:02}:{mins:02}:{secs:02}"

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Podcast keyword finder')
    parser.add_argument('-f', '--file', help='Path to the podcast audio file')
    parser.add_argument('-k', '--keywords', nargs='+', default=["technology", "AI", "economy"],
                        help='Keywords to search for (space-separated)')
    args = parser.parse_args()

    # Get input file path
    input_podcast = args.file
    if not input_podcast:
        print("Please select your podcast file...")
        input_podcast = select_file()
        if not input_podcast:
            print("No file selected. Exiting...")
            return

    converted_audio = "converted_podcast.wav"
    keywords = args.keywords

    print(f"Using file: {input_podcast}")
    print(f"Searching for keywords: {', '.join(keywords)}")

    # Check if input file exists
    if not os.path.exists(input_podcast):
        print(f"Error: Input file '{input_podcast}' not found.")
        return

    # Step 1: Convert audio
    if not convert_audio(input_podcast, converted_audio):
        return

    # Step 2: Transcribe audio
    transcription = transcribe_audio(converted_audio)

    # Step 3: Find keywords
    occurrences = find_keywords(transcription, keywords)

    # Display results
    if occurrences:
        print("Keyword occurrences:")
        for occ in occurrences:
            time_formatted = format_time(occ['time'])
            print(f"Keyword '{occ['keyword']}' found at {time_formatted}")
    else:
        print("No keywords found.")

if __name__ == "__main__":
    main()