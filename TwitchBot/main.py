# source /home/sodiumtf/Downloads/Programming/PythonScripts/bopItTwitchBot/venv/bin/activate
# cd /home/sodiumtf/Downloads/Programming/PythonScripts/bopItTwitchBot

# Imports
from twitchAPI.chat import Chat, EventData, ChatCommand
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch
import asyncio

import random, time, pygame, serial, os

# Constant variables
APP_ID = 'xxxxx'
APP_SECRET = 'xxxxxx'
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CHANNEL_MANAGE_BROADCAST]
TARGET_CHANNEL = 'xxxxxxx'
SCORE_FILE = '/home/sodiumtf/Downloads/Programming/PythonScripts/bopItTwitchBot/score.txt'
MINIMUM_TIME_BETWEEN_PROMPTS = 5

# Game variables
successes = 0
fails = 0
promptsSinceLastFail = 0
lastBopItTime = 0

# Serial setup
SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 9600
arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

# Pygame setup
pygame.mixer.init()

# Sound files
SOUND_FILES = {
    'bop': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/bopIt.mp3',
    'twist': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/twistIt.mp3',
    'pull': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/pullIt.mp3',
    'fail': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/fail.mp3',
    'bophit': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/bopHit.mp3',
    'twisthit': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/twistHit.mp3',
    'pullhit': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/pullHit.mp3',
}

# Preload sounds
sounds = {name: pygame.mixer.Sound(path) for name, path in SOUND_FILES.items()}

# Function Definitions
def play_sound(file):
    sounds[file].play()

def load_score():
    global successes, fails, promptsSinceLastFail
  
    with open(SCORE_FILE, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("Successes:"):
                successes = int(line.split(":")[1].strip())
            elif line.startswith("Fails:"):
                fails = int(line.split(":")[1].strip())

def save_score():
    with open(SCORE_FILE, 'w') as f:
        f.write(f"Successes: {successes}\nFails: {fails}\nPrompts since last fail: {promptsSinceLastFail}\n")

# Bot connected succesfully
async def on_ready(ready_event: EventData):
    await ready_event.chat.join_room(TARGET_CHANNEL)
    print(f'Bot has joined {TARGET_CHANNEL} channel!')

# Bop it send command
async def bop_it_command(cmd: ChatCommand):
    global lastBopItTime, successes, fails, promptsSinceLastFail
    now = time.time()

    if(now - lastBopItTime) >= MINIMUM_TIME_BETWEEN_PROMPTS:
        lastBopItTime = now
    
        action = random.choice(['bop', 'twist', 'pull'])

        # Send chat message confirming command
        await cmd.reply(f'Sent bop it prompt: {action}')
        
        # Clear buffer
        arduino.reset_input_buffer()

        # Send to Arduino
        arduino.write((action + "\n").encode("utf-8"))

        # Play corresponding sound
        play_sound('' + action)

        # Listen for Arduino response (success/fail)
        response = None
        start_time = time.time()
        while time.time() - start_time < 6:  # wait up to 6 seconds
            if arduino.in_waiting > 0:
                response = arduino.readline().decode("utf-8").strip()
                break
            await asyncio.sleep(0.1)  # check every 100ms

        if response:
            if response.lower() == "fail":
                play_sound('fail')
                fails += 1
                promptsSinceLastFail = 0
            elif response.lower() == "success":
                if action == "bop":
                    play_sound('bophit')
                elif action == "twist":
                    play_sound('twisthit')
                elif action == "pull":
                    play_sound('pullhit')
                successes += 1
                promptsSinceLastFail += 1

        save_score()

# bot setup
async def run_bot():
    load_score()

    bot = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(bot, USER_SCOPE)
    token, refresh_token = await auth.authenticate()
    await bot.set_user_authentication(token, USER_SCOPE, refresh_token)

    chat = await Chat(bot)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_command('bopit', bop_it_command)

    chat.start()

asyncio.run(run_bot())