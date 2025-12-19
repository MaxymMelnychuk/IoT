from phew import server, access_point
from machine import Pin, PWM
import utime
import json
import _thread

# Création du point d'accès
ap = access_point("Maxym2", "123456789")
ip = ap.ifconfig()[0]
print("IP du serveur :", ip)

# Lecture de la page HTML
with open("index.html", "r") as page:
    indexhtml = page.read()

# Initialisation buzzer et LED RGB
buzzer = PWM(Pin(17))
led_red = Pin(2, Pin.OUT)
led_green = Pin(4, Pin.OUT)

# Notes de base
notes = {
    'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349,
    'G4': 392, 'A4': 440, 'B4': 494, 'C5': 523,
    'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784,
    'A5': 880, 'B5': 988, 'C6': 1047
}

# 3 mélodies différentes
melodies = [
    # Hymne de l'Union Soviétique (version simplifiée)
    {
        'melody': [
            'C5','G4','E4','F4','D4','C4','C4','D4',
            'E4','F4','G4','C5','B4','G4','F4','E4',
            'D4','C4','C4','G4','E4','F4','D4','C4'
        ],
        'durations': [
            0.6,0.4,0.4,0.4,0.4,0.4,0.4,0.4,
            0.4,0.4,0.4,0.6,0.4,0.4,0.4,0.4,
            0.4,0.4,0.6,0.4,0.4,0.4,0.4,1.2
        ]
    },
    # Mary had a little lamb
    {
        'melody': ['E4','D4','C4','D4','E4','E4','E4','D4','D4','D4','E4','G4','G4'],
        'durations':[0.4]*13
    },
    # Red Sun in the Sky (approximation)
    {
        'melody': [
            'G4','G4','A4','G4','F4','E4','D4',
            'E4','F4','G4','A4','G4','F4','E4',
            'G4','A4','B4','A4','G4','F4','E4',
            'D4','E4','F4','G4','A4','G4','F4'
        ],
        'durations': [0.4] * 28
    }
]

# Variables d'état
music_playing = False
current_song = 0
skip_song = False

# Fonction pour jouer une note
def play_tone(freq, duration):
    buzzer.freq(freq)
    buzzer.duty_u16(32768)
    utime.sleep(duration)
    buzzer.duty_u16(0)
    utime.sleep(0.05)

# Fonction principale pour jouer les musiques en boucle
def play_melody_loop():
    global music_playing, current_song, skip_song
    music_playing = True
    led_green.on()
    led_red.off()
    while music_playing:
        song = melodies[current_song]
        melody = song['melody']
        durations = song['durations']
        for i, note in enumerate(melody):
            if not music_playing or skip_song:
                break
            if note in notes:
                play_tone(notes[note], durations[i])
        utime.sleep(0.2)
        if skip_song:
            skip_song = False
            current_song = (current_song + 1) % len(melodies)
    led_green.off()
    led_red.on()
    buzzer.deinit()

# Routes API (ON/OFF/NEXT)
@server.route("/", methods=["GET"])
def home(request):
    return indexhtml

@server.route("/music/<param>", methods=["GET"])
def command(request, param):
    global music_playing, current_song, skip_song
    if param == "on":
        if not music_playing:
            _thread.start_new_thread(play_melody_loop, ())
        return json.dumps({"status": "playing", "song": current_song})
    elif param == "off":
        music_playing = False
        skip_song = False
        buzzer.deinit()
        led_green.off()
        led_red.on()
        return json.dumps({"status": "stopped"})
    elif param == "next":
        if music_playing:
            skip_song = True
        else:
            current_song = (current_song + 1) % len(melodies)
        return json.dumps({"status": "next", "song": current_song})
    else:
        return "Not found", 404

@server.catchall()
def catchall(request):
    return "Not found", 404

# Bouton pour chanson suivante sur pin 6
button = Pin(6, Pin.IN, Pin.PULL_UP)
def button_handler(pin):
    global skip_song, current_song, music_playing
    if music_playing:
        skip_song = True
    else:
        current_song = (current_song + 1) % len(melodies)
    print("Chanson suivante:", current_song)
button.irq(trigger=Pin.IRQ_FALLING, handler=button_handler)

# LED rouge au démarrage
led_red.on()
led_green.off()

server.run()

