import cv2
import numpy as np
import zipfile
import os
import subprocess
import re
import tkinter as tk
from tkinter import filedialog


def select_zip_file():
    root = tk.Tk()
    root.withdraw()
    zip_filename = filedialog.askopenfilename(initialdir="/home/sujit/Desktop/omniverse gymn frozen envs", title="Select the ZIP file", filetypes=[("ZIP files", "*.zip")])
    return zip_filename


def get_duration(video_path):
    """Get the duration of a video using FFmpeg."""
    cmd = ["ffmpeg", "-i", video_path, "-hide_banner"]
    output = subprocess.Popen(cmd, stderr=subprocess.PIPE).communicate()[1].decode('utf-8')
    pattern = r"Duration: (\d+):(\d+):(\d+\.\d+)"
    match = re.search(pattern, output)
    if not match:
        raise ValueError("Couldn't determine video duration.")
    hours, minutes, seconds = map(float, match.groups())
    return 3600 * hours + 60 * minutes + seconds


def is_similar(img1, img2, threshold=0.5):
    """ Check if two images are similar based on a threshold """
    diff = cv2.absdiff(img1, img2)
    return np.mean(diff) < threshold


def process_video(video_path, output_path):
    video_duration = get_duration(video_path)

    frames = []
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    ret, prev_frame = cap.read()
    consecutive_similar = 0  # Counter for consecutive similar frames

    while ret:
        ret, frame = cap.read()
        if ret:
            if is_similar(prev_frame, frame):
                consecutive_similar += 1
            else:
                # If there were fewer than 3 consecutive similar frames, add them to the output list
                if 0 < consecutive_similar < 5:
                    frames.extend([prev_frame] * consecutive_similar)
                # Reset the counter and add the current frame
                consecutive_similar = 0
                frames.append(prev_frame)
            prev_frame = frame

    # Handle the tail end of the video
    if frame is not None:
        if consecutive_similar < 5:
            frames.extend([frame] * (consecutive_similar + 1))
        else:
            frames.append(frame)

    # Adjust the duration by the proportion of retained frames
    adjusted_duration = video_duration * (len(frames) / total_frames)
    # Calculate the new FPS to match the adjusted video duration
    new_fps = len(frames) / adjusted_duration

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, new_fps, (int(cap.get(3)), int(cap.get(4))))

    for frame in frames:
        out.write(frame)

    cap.release()
    out.release()


def remove_freezes(zip_filename):
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith(('.mkv', '.mp4')):
                zip_ref.extract(file)
                file_extension = file.split('.')[-1]
                output_file = file[:-len(file_extension)-1] + "_nofreeze." + file_extension
                process_video(file, output_file)
                os.remove(file)

                # Add the processed file back to the zip
                with zipfile.ZipFile(zip_filename, 'a') as mod_zip:
                    mod_zip.write(output_file)

                os.remove(output_file)



if __name__ == "__main__":
    zip_file = select_zip_file()
    if zip_file:
        remove_freezes(zip_file)
