import logging
from tiktok_uploader.upload import upload_video

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the video file and description
FILENAME = "AITA_2_WITH_SUBS.mp4"  # Change this path to your video file
DESCRIPTION = "This is a #cool video I just downloaded. #wow #cool check it out on @tiktok"

def main():
    try:
        logging.info("Starting the upload process.")
        logging.debug(f"Uploading video: {FILENAME} with description: {DESCRIPTION}")

        # Upload the video
        upload_video(FILENAME, description=DESCRIPTION, cookies="Cookies/cookies.txt")

        logging.info("Upload completed successfully.")
    except Exception as e:
        logging.error(f"Failed to upload video: {e}")

if __name__ == "__main__":
    main()
