#!/usr/bin/env python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import time
import vlc # VLC must be installed for this to work, as well as the Python biding (pip install python-vlc)

# VLC objects - see https://forum.videolan.org/viewtopic.php?f=32&t=152290
# We use ALSA output - system volume can be changed with alsamixer && sudo alsactl store
vlc_instance = vlc.Instance("--quiet", "--aout=alsa")
vlc_player = vlc_instance.media_player_new()

# Constants
PIN_ROTARY_CLK = 17 # BCM pin 17, physical pin 11 (https://pinout.xyz/pinout/pin11_gpio17)
PIN_ROTARY_DT = 18 # BCM pin 18, physical pin 12 (https://pinout.xyz/pinout/pin12_gpio18)
PIN_ROTARY_SW = 27 # BCM pin 27, physical pin 13 (https://pinout.xyz/pinout/pin13_gpio27)
RADIO_URLS = [
    "http://direct.franceculture.fr/live/franceculture-midfi.mp3",
    "https://scdn.nrjaudio.fm/audio1/fr/30601/mp3_128.mp3?origine=ubuntu_website",
    "http://mfm.ice.infomaniak.ch/mfm-128.mp3",
] # borrowed from https://doc.ubuntu-fr.org/liste_radio_france

# Global variables
global_last_rotary_selection = (0, 1, 1)
global_last_radio_selection = 0

def reload_vlc():
    """ Reload the VLC player by reading the global index. """
    selected_radio_url = RADIO_URLS[global_last_radio_selection]
    print("Playing radio {}".format(selected_radio_url))
    vlc_player.set_media(
        vlc_instance.media_new(selected_radio_url)
    )
    vlc_player.play()

def init_gpio():
    GPIO.setwarnings(True)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_ROTARY_CLK, GPIO.IN)
    GPIO.setup(PIN_ROTARY_DT, GPIO.IN)
    GPIO.setup(PIN_ROTARY_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP) # see http://codelectron.com/rotary-encoder-with-raspberry-pi/
    GPIO.add_event_detect(PIN_ROTARY_CLK, GPIO.RISING, callback=rotary_rotation_callback) # no bouncetime
    GPIO.add_event_detect(PIN_ROTARY_DT, GPIO.RISING, callback=rotary_rotation_callback) # no bouncetime
    GPIO.add_event_detect(PIN_ROTARY_SW, GPIO.FALLING, callback=rotary_switch_callback, bouncetime=300) # see http://codelectron.com/rotary-encoder-with-raspberry-pi/

def rotary_switch_callback(channel):
    """ Rotary switch callback """
    print("Pausing/playing player")
    vlc_player.pause()

def rotary_rotation_callback(channel):
    """ Rotary rotation handler.
    See https://www.raspberrypi.org/forums/viewtopic.php?t=140250
    """
    
    # Allow editing of the global variables
    global global_last_rotary_selection
    global global_last_radio_selection

    if channel == PIN_ROTARY_CLK:
        current_rotary_selection = (PIN_ROTARY_CLK, 1, GPIO.input(PIN_ROTARY_DT))
    else:
        current_rotary_selection = (PIN_ROTARY_DT, GPIO.input(PIN_ROTARY_CLK), 1)

    if current_rotary_selection == (PIN_ROTARY_CLK, 1, 1) and global_last_rotary_selection[1] == 0:
        # Rotary is down
        print("Rotary is down")
        global_last_radio_selection = global_last_radio_selection - 1 if global_last_radio_selection > 0 else len(RADIO_URLS) - 1
        reload_vlc()
    elif current_rotary_selection == (PIN_ROTARY_DT, 1, 1) and global_last_rotary_selection[2] == 0:
        # Rotary is up
        print("Rotary is up")
        global_last_radio_selection = global_last_radio_selection + 1 if global_last_radio_selection < len(RADIO_URLS) - 1 else 0
        reload_vlc()
    
    global_last_rotary_selection = current_rotary_selection

# Init and loop forever (stop with CTRL+C)
reload_vlc()
init_gpio()


while True:
    time.sleep(1)