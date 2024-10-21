#wonderful
import random
from moviepy.editor import VideoFileClip, AudioFileClip
from pydub import AudioSegment

# Paths to media files
AUDIO_FILE_PATH = "Moutput.mp3"
VIDEO_FILE_PATH = "ShortFormGen/Content/MC/mc-1.mp4"
OUTPUT_VIDEO_FILE_PATH = "output_video_vertical.mp4"

# Function to get duration of the audio file in seconds
def get_audio_duration(audio_file_path):
    audio = AudioSegment.from_file(audio_file_path)
    return len(audio) / 1000  # Convert milliseconds to seconds

# Function to extract a random part of the video with the given duration
def extract_random_video_clip(video_file_path, duration):
    video = VideoFileClip(video_file_path)
    
    # Ensure the start time is within the valid range
    max_start_time = video.duration - duration
    if max_start_time <= 0:
        raise ValueError("The video is shorter than the audio duration.")
    
    # Random start time within the valid range
    start_time = random.uniform(0, max_start_time)
    end_time = start_time + duration

    # Extract the random clip
    video_clip = video.subclip(start_time, end_time)
    
    # Crop to vertical (9:16 aspect ratio)
    video_clip = crop_to_vertical(video_clip)

    return video_clip

# Function to crop video to 9:16 aspect ratio (for vertical format)
def crop_to_vertical(video_clip):
    # Calculate target aspect ratio (9:16 is the standard vertical aspect ratio)
    target_aspect_ratio = 9 / 16
    
    # Get original video dimensions
    original_width, original_height = video_clip.size
    
    # Determine new width for the desired vertical crop
    new_width = int(original_height * target_aspect_ratio)
    
    # If the original width is larger than the target width, crop horizontally
    if original_width > new_width:
        x_center = original_width // 2
        x1 = x_center - new_width // 2
        x2 = x_center + new_width // 2
        video_clip = video_clip.crop(x1=x1, x2=x2)
    else:
        raise ValueError("The video is too narrow to be cropped to a vertical format.")
    
    return video_clip

# Main script logic
def main():
    try:
        # Get the duration of the audio
        audio_duration = get_audio_duration(AUDIO_FILE_PATH)
        print(f"Audio duration: {audio_duration} seconds")

        # Extract a random part of the video with the same duration as the audio
        video_clip = extract_random_video_clip(VIDEO_FILE_PATH, audio_duration)

        # Load the audio file
        audio_clip = AudioFileClip(AUDIO_FILE_PATH)

        # Set the extracted audio to the video clip
        video_clip = video_clip.set_audio(audio_clip)

        # Export the final vertical video with audio
        video_clip.write_videofile(OUTPUT_VIDEO_FILE_PATH, codec="libx264", audio_codec="aac")

        print(f"Final vertical video saved to {OUTPUT_VIDEO_FILE_PATH}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
