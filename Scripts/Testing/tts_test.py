#WORKING REALLY WELL AND EASY TO USE
import asyncio
import edge_tts
import os


# File path for the text file
TEXT_FILE_PATH = 'TXT/script.txt'

print('Text to Speech Test')
print('-------------------')
print('Text file path:', TEXT_FILE_PATH)

# Load text from the file
with open(TEXT_FILE_PATH, 'r', encoding='utf-8') as file:
    TEXT = file.read()

FEMALE_VOICES = [
    'en-AU-NatashaNeural',   # Australia [0]
    'en-US-JennyNeural',     # United States [1] - 
    'en-GB-LibbyNeural',     # United Kingdom [2] -
    'en-AU-HayleyNeural',    # Australia [3]
    'en-US-AriaNeural',      # United States [4] -
    'en-GB-MaisieNeural',    # United Kingdom [5] -
    'en-AU-MadelineNeural',  # Australia [6]
    'en-US-AmberNeural',     # United States [7]
    'en-GB-SoniaNeural'      # United Kingdom [8] -
]

MALE_VOICES = [
    'en-AU-WilliamNeural',   # Australia [0]
    'en-US-GuyNeural',       # United States [1] - GOOD Default
    'en-GB-RyanNeural',      # United Kingdom [2] 
    'en-AU-JasonNeural',     # Australia [3]
    'en-US-EricNeural',      # United States [4] -
    'en-AU-CarlNeural',      # Australia [5]
    'en-US-RogerNeural',     # United States [6]
    'en-GB-ThomasNeural',    # United Kingdom [7] 
]


VOICE = MALE_VOICES[1]
OUTPUT = 'Moutput.mp3'

async def main() -> None:
    communicate =  edge_tts.Communicate(TEXT,VOICE, rate='+15%')
    await communicate.save(OUTPUT)
    print(f'Audio saved to {OUTPUT}')

loop = asyncio.get_event_loop_policy().get_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
