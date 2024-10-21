import whisper
import os
import subprocess
import shutil
import cv2
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip
from tqdm import tqdm
import numpy as np
from PIL import Image, ImageFont, ImageDraw

# Define constants for font and its properties
FONT_PATH = "Fonts/Gilroy-Bold.ttf"  # Update this with the path to your custom font
FONT_SIZE = 34  # Increased font size for better visibility
OUTLINE_THICKNESS = 2
TEXT_COLOR = (254, 227, 0)  # Custom yellow color for text
OUTLINE_COLOR = (0, 0, 0)  # Black color for outline
MAX_LINE_WIDTH = 30  # Max characters per line before splitting text

class VideoTranscriber:
    def __init__(self, video_path, model_size='base'):
        self.model = whisper.load_model(model_size)  # Load the default Whisper model
        self.video_path = video_path
        self.audio_path = ''
        self.text_array = []
        self.fps = 0
        self.font = ImageFont.truetype(FONT_PATH, FONT_SIZE)  # Load font once

    def transcribe_video(self):
        print('Transcribing video')
        # Ensure the audio is extracted and used properly
        result = self.model.transcribe(self.audio_path)
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        asp = 16 / 9
        
        # Adjust width based on aspect ratio
        ret, frame = cap.read()
        if not ret:
            raise ValueError("Could not read video frame")
        width = frame[:, int((width - 1 / asp * height) / 2):width - int((width - 1 / asp * height) / 2)].shape[1]
        width = int(width - (width * 0.1))
        self.fps = cap.get(cv2.CAP_PROP_FPS)

        for j in tqdm(result["segments"]):
            lines = []
            text = j["text"]
            end = j["end"]
            start = j["start"]
            total_frames = int((end - start) * self.fps)
            start = start * self.fps
            total_chars = len(text)
            words = text.split(" ")
            i = 0

            while i < len(words):
                words[i] = words[i].strip()
                if words[i] == "":
                    i += 1
                    continue
                line = words[i]
                remaining_pixels = width - self.get_text_width(line)

                while remaining_pixels > 0:
                    i += 1 
                    if i >= len(words):
                        break
                    remaining_pixels -= self.get_text_width(words[i])
                    if remaining_pixels >= 0:
                        line += " " + words[i]

                # Split long lines into multiple lines for better readability
                if len(line) > MAX_LINE_WIDTH:
                    line = self.split_line(line)

                line_array = [line, int(start) + 15, int(len(line) / total_chars * total_frames) + int(start) + 15]
                start = int(len(line) / total_chars * total_frames) + int(start)
                lines.append(line_array)
                self.text_array.append(line_array)

        cap.release()
        print('Transcription complete')

    def split_line(self, line):
        """Split the line into multiple lines if it exceeds the max width."""
        words = line.split(" ")
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + word) > MAX_LINE_WIDTH:
                lines.append(current_line.strip())
                current_line = word + " "
            else:
                current_line += word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        return "\n".join(lines)

    def extract_audio(self):
        print('Extracting audio from video')
        video = VideoFileClip(self.video_path)
        audio = video.audio

        # Ensure the audio path has the correct extension
        self.audio_path = os.path.splitext(self.video_path)[0] + ".mp3"
        
        try:
            # Write the audio file and check if it was created
            audio.write_audiofile(self.audio_path, codec='libmp3lame')
            print("Audio extracted successfully.")
        except Exception as e:
            print(f"Audio extraction failed: {e}")

    def draw_text_with_outline(self, frame, text, position):
        """Draw text with an outline on the image frame."""
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(frame_pil)

        # Calculate text size using getbbox
        text_bbox = draw.textbbox((0, 0), text, font=self.font)
        text_size = (text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1])  # (width, height)

        # Calculate position for center alignment
        centered_position = (position[0] - text_size[0] // 2, position[1])

        # Draw outline by drawing the text in outline color with offsets
        for dx in range(-OUTLINE_THICKNESS, OUTLINE_THICKNESS + 1):
            for dy in range(-OUTLINE_THICKNESS, OUTLINE_THICKNESS + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((centered_position[0] + dx, centered_position[1] + dy), text, font=self.font, fill=OUTLINE_COLOR)

        # Draw the main text
        draw.text(centered_position, text, font=self.font, fill=TEXT_COLOR)

        # Convert back to OpenCV format
        return cv2.cvtColor(np.array(frame_pil), cv2.COLOR_RGB2BGR)

    def extract_frames(self, output_folder):
        print('Extracting frames')
        cap = cv2.VideoCapture(self.video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        asp = width / height
        N_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = frame[:, int(int(width - 1 / asp * height) / 2):width - int((width - 1 / asp * height) / 2)]

            for i in self.text_array:
                if N_frames >= i[1] and N_frames <= i[2]:
                    text = i[0]
                    text_lines = text.splitlines()  # Split text into lines
                    y_offset = int(height / 2)  # Starting y position for the text

                    for line in text_lines:
                        # Draw each line centered
                        frame = self.draw_text_with_outline(frame, line, (width // 2, y_offset))
                        y_offset += FONT_SIZE + 5  # Move down for the next line (add extra space between lines)

                    break

            cv2.imwrite(os.path.join(output_folder, f"{N_frames}.jpg"), frame)
            N_frames += 1

        cap.release()
        print('Frames extracted')

    def create_video(self):
        print('Creating video')
        image_folder = os.path.join(os.path.dirname(self.video_path), "frames")
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        self.extract_frames(image_folder)

        images = [img for img in os.listdir(image_folder) if img.endswith(".jpg")]
        images.sort(key=lambda x: int(x.split(".")[0]))

        output_video_path = os.path.splitext(self.video_path)[0] + "_WITH_SUBS_V2.mp4"

        clip = ImageSequenceClip([os.path.join(image_folder, image) for image in images], fps=self.fps)
        audio = AudioFileClip(self.audio_path)

        # Set audio to clip
        clip = clip.set_audio(audio)
        
        # Write video file with audio codec settings
        clip.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

        shutil.rmtree(image_folder)
        os.remove(self.audio_path)
        print(f'Video created: {output_video_path}')

    def get_text_width(self, text):
        """Get the width of the text."""
        return self.font.getbbox(text)[2] - self.font.getbbox(text)[0]

# Entry point for testing purposes
def main():
    video_path = "aita_TEST2.mp4"  # Update with your actual video path

    # Initialize transcriber with the base model
    transcriber = VideoTranscriber(video_path)
    
    transcriber.extract_audio()
    transcriber.transcribe_video()
    transcriber.create_video()

if __name__ == "__main__":
    main()
