# source /home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/venv/bin/activate
# cd /home/sodiumtf/Downloads/Programming/PythonScripts/bopIt

# Imports
import random, time, pygame, serial

# Constant Variables
SCORE_FILE = '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/score.txt'
MINIMUM_TIME = 0.75
DECREMENT_PER_PROMPT = 0.0025  
STARTING_TIME = 1.0
VOLUME_STEP = 0.33
VOLUME_MAX = 1.0

# Game variables
gameState = 0
score = 0
volume = 1.0

# Serial Setup
SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 9600
arduino = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

# Pygame Setup
pygame.mixer.init()

# Sound Files
SOUND_FILES = {
    'bop': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/bopIt.mp3',
    'twist': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/twistIt.mp3',
    'pull': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/pullIt.mp3',
    'fail': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/fail.mp3',
    'bophit': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/bopHit.mp3',
    'twisthit': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/twistHit.mp3',
    'pullhit': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/pullHit.mp3',
    'intro': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/intro.mp3',
    'volume': '/home/sodiumtf/Downloads/Programming/PythonScripts/bopIt/soundEffects/volume.mp3',
}

# Preload sounds
sounds = {name: pygame.mixer.Sound(path) for name, path in SOUND_FILES.items()}

# Function Definitions
def play_sound(file):
    sounds[file].play()

def volume_control():
    global sounds, volume
    for sound in sounds.values():
        sound.set_volume(volume)
    play_sound('volume')
    
def update():  
    # Update score file
    with open(SCORE_FILE, 'w') as f:
        f.write(f"Score: {score}")
    # Update time variable
    calc_timing(score)

def wait_for_arduino():
    while True:
        if arduino.in_waiting > 0:
            return arduino.readline().decode("utf-8").strip()
        time.sleep(0.05)

def calc_timing(score):
    global window
    decrement_per_prompt_function = -(DECREMENT_PER_PROMPT) * score + STARTING_TIME
    window = max(MINIMUM_TIME, decrement_per_prompt_function)

# Initial Load
update()

# Main Loop
while True:
    if gameState == 1:
        action = random.choice(['bop', 'twist', 'pull'])

        arduino.reset_input_buffer()

        # Send to Arduino
        arduino.write((action + "\n").encode("utf-8"))

        # Play corresponding sound
        play_sound(action)

        # Listen for Arduino response (success/fail)
        response = wait_for_arduino()

        if response.lower() == "fail":
            play_sound('fail')
            gameState = 0
            score = 0
        elif response.lower() == "success":
            if action == "bop":
                play_sound('bophit')
            elif action == "twist":
                play_sound('twisthit')
            elif action == "pull":
                play_sound('pullhit')
            score += 1

        if gameState == 1:
            update()
            time.sleep(window)
        if gameState == 0:
            time.sleep(2)
            arduino.reset_input_buffer()

    if gameState == 0:
        # Listen to arduino
        response = wait_for_arduino()

        # Start game logic
        if response == "start":
            gameState = 1
            update()
            play_sound('intro')
            time.sleep(2)

        # Volume control logic
        if response == "volume":
            volume += VOLUME_STEP
            if volume > VOLUME_MAX:
                volume = VOLUME_STEP
            volume_control()

    time.sleep(0.05) 

