import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyaudio
import wave
import tkinter as tk
from tkinter import filedialog
import threading
import time

class SimpleVisualizer:
    def __init__(self, master):
        self.master = master
        self.master.title("Simple Audio Visualizer")
        self.master.geometry("800x400")

        self.file_path = None
        self.is_playing = False
        self.peak_amplitudes = []
        self.peak_times = []

        self.select_button = tk.Button(master, text="Select WAV File", command=self.select_file)
        self.select_button.pack(pady=5)

        self.play_button = tk.Button(master, text="Play/Pause", command=self.toggle_play, state=tk.DISABLED)
        self.play_button.pack(pady=5)

        self.fig, self.ax = plt.subplots(figsize=(8, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.scatter = self.ax.scatter([], [], c='r', s=2)
        self.ax.set_title("Peak Amplitude per Second")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Peak Amplitude")
        self.ax.set_ylim(0, 32767)

        self.p = pyaudio.PyAudio()
        self.stream = None

    def select_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if self.file_path:
            self.play_button.config(state=tk.NORMAL)
            self.setup_audio()

    def setup_audio(self):
        self.wf = wave.open(self.file_path, 'rb')
        self.stream = self.p.open(
            format=self.p.get_format_from_width(self.wf.getsampwidth()),
            channels=self.wf.getnchannels(),
            rate=self.wf.getframerate(),
            output=True
        )
        self.duration = self.wf.getnframes() / self.wf.getframerate()
        self.ax.set_xlim(0, self.duration)

    def toggle_play(self):
        if self.is_playing:
            self.is_playing = False
            self.play_button.config(text="Play")
        else:
            self.is_playing = True
            self.play_button.config(text="Pause")
            self.peak_amplitudes = []
            self.peak_times = []
            self.wf.rewind()
            threading.Thread(target=self.play_audio).start()
            threading.Thread(target=self.update_visualization).start()

    def play_audio(self):
        while self.is_playing:
            data = self.wf.readframes(self.wf.getframerate() // 20)  # 50ms chunks
            if len(data) == 0:
                self.is_playing = False
                self.play_button.config(text="Play")
                break
            self.stream.write(data)
            audio_data = np.frombuffer(data, dtype=np.int16)

            if self.wf.getnchannels() == 2:
                audio_data = np.mean(audio_data.reshape((-1, 2)), axis=1)

            current_max = np.max(np.abs(audio_data))
            current_time = self.wf.tell() / self.wf.getframerate()

            self.peak_amplitudes.append(current_max)
            self.peak_times.append(current_time)

    def update_visualization(self):
        while self.is_playing:
            if self.peak_times and self.peak_amplitudes:
                self.scatter.set_offsets(np.c_[self.peak_times, self.peak_amplitudes])
                self.ax.set_xlim(0, self.duration)
                self.ax.set_ylim(0, max(self.peak_amplitudes + [32767]))
                self.canvas.draw()
                self.canvas.flush_events()
            time.sleep(0.05)

    def close(self):
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        self.master.quit()

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleVisualizer(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()