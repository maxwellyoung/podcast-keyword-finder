import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import ffmpeg
import whisper
import nltk
import os
from pathlib import Path

class PodcastKeywordFinderGUI:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        self.processing = False
        self.current_transcription = None

    def setup_window(self):
        self.root.title("Podcast Keyword Finder")
        self.root.geometry("800x700")
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 800) // 2
        y = (screen_height - 700) // 2
        self.root.geometry(f"800x700+{x}+{y}")

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Helvetica", 24, "bold"))
        style.configure("Header.TLabel", font=("Helvetica", 14))
        style.configure("Status.TLabel", font=("Helvetica", 12))

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Title
        title = ttk.Label(main_frame, text="Podcast Keyword Finder", style="Title.TLabel")
        title.pack(pady=(0, 20))

        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Select Podcast", padding="10")
        file_frame.pack(fill="x", pady=(0, 10))

        self.file_path = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path, width=50)
        file_entry.pack(side="left", padx=5)

        browse_button = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side="left")

        # Keywords
        keywords_frame = ttk.LabelFrame(main_frame, text="Keywords", padding="10")
        keywords_frame.pack(fill="x", pady=(0, 10))

        self.keywords_text = scrolledtext.ScrolledText(keywords_frame, height=3)
        self.keywords_text.pack(fill="x")
        self.keywords_text.insert("1.0", "technology, AI, economy")

        # Model selection
        model_frame = ttk.LabelFrame(main_frame, text="Model", padding="10")
        model_frame.pack(fill="x", pady=(0, 10))

        self.model_var = tk.StringVar(value="tiny")
        models = [("Tiny (Fastest)", "tiny"), 
                 ("Base (Balanced)", "base"),
                 ("Small (Most Accurate)", "small")]

        for text, value in models:
            ttk.Radiobutton(model_frame, text=text, value=value, 
                          variable=self.model_var).pack(anchor="w")

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))

        self.process_button = ttk.Button(button_frame, text="Process Podcast", 
                                       command=self.process_podcast)
        self.process_button.pack(side="left", padx=5)

        self.cancel_button = ttk.Button(button_frame, text="Cancel", 
                                      command=self.cancel_processing, state="disabled")
        self.cancel_button.pack(side="left")

        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                      maximum=100, mode='determinate')
        self.progress.pack(fill="x", pady=(0, 5))

        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                    style="Status.TLabel")
        self.status_label.pack()

        # Results
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.results_text = scrolledtext.ScrolledText(results_frame)
        self.results_text.pack(fill="both", expand=True)

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Podcast File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.aac"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.file_path.set(file_path)

    def update_status(self, message, progress=None):
        self.status_var.set(message)
        if progress is not None:
            self.progress_var.set(progress)
        self.root.update_idletasks()

    def process_podcast(self):
        if not self.file_path.get():
            self.update_status("Please select a podcast file first!")
            return

        self.process_button.state(['disabled'])
        self.cancel_button.state(['!disabled'])
        self.results_text.delete('1.0', tk.END)
        
        thread = threading.Thread(target=self.process_podcast_thread)
        thread.daemon = True
        thread.start()

    def process_podcast_thread(self):
        try:
            self.processing = True
            input_podcast = self.file_path.get()
            converted_audio = "converted_podcast.wav"
            
            self.update_status("Converting audio...", 10)
            if not self.convert_audio(input_podcast, converted_audio):
                return

            self.update_status("Loading Whisper model...", 30)
            model = whisper.load_model(self.model_var.get())
            
            self.update_status("Transcribing audio (this may take several minutes)...", 40)
            result = model.transcribe(converted_audio, word_timestamps=True)
            
            self.update_status("Finding keywords...", 80)
            keywords = [k.strip() for k in self.keywords_text.get("1.0", tk.END).strip().split(",")]
            occurrences = self.find_keywords(result, keywords)
            
            self.display_results(occurrences)
            self.update_status("Processing complete!", 100)
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
        finally:
            self.processing = False
            self.process_button.state(['!disabled'])
            self.cancel_button.state(['disabled'])
            if os.path.exists(converted_audio):
                try:
                    os.remove(converted_audio)
                except:
                    pass

    def convert_audio(self, input_path, output_path):
        try:
            (
                ffmpeg
                .input(input_path)
                .output(output_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000')
                .overwrite_output()
                .run(quiet=True)
            )
            return True
        except ffmpeg.Error as e:
            self.update_status(f"FFmpeg error: {e}")
            return False

    def find_keywords(self, transcription, keywords):
        keyword_occurrences = []
        for segment in transcription['segments']:
            text = segment.get('text', '').lower()
            for keyword in keywords:
                if keyword.lower() in text:
                    start = segment['start']
                    keyword_occurrences.append({
                        'keyword': keyword,
                        'time': start,
                        'context': text
                    })
        return keyword_occurrences

    def format_time(self, seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hrs:02}:{mins:02}:{secs:02}"

    def display_results(self, occurrences):
        self.results_text.delete('1.0', tk.END)
        if occurrences:
            self.results_text.insert(tk.END, "Found keywords:\n\n")
            for occ in occurrences:
                time = self.format_time(occ['time'])
                self.results_text.insert(tk.END, 
                    f"• {occ['keyword']} at {time}\n"
                    f"  Context: {occ['context']}\n\n")
        else:
            self.results_text.insert(tk.END, "No keywords found.")

    def cancel_processing(self):
        self.processing = False
        self.update_status("Cancelling...")

def main():
    nltk.download('punkt')
    root = tk.Tk()
    app = PodcastKeywordFinderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 