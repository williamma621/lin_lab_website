from tkinter import Tk
from tkinter.filedialog import askopenfilename


def ask_openfilename():

    Tk().withdraw()  # Hide the root tkinter window
    input_video_path = askopenfilename(
        title="Select a video file",
        filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv")]
    )
    if not input_video_path:
        print("No input file selected. Exiting.")
        exit()
    return input_video_path

if __name__ == "__main__":
    input_video_path = ask_openfilename()
    print(f"Selected video file: {input_video_path}")