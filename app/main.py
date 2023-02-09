"""
Simple beat visualiser for Windows.
Based on fetching output audio going through Stereo Mix device
(needs to be enabled in Settings >> System >> Sound >> Manage sound devices)
Application's options:
KEY | Result
 Q    Previous song
 E    Next song
 >||  Resets max/min beat range
 A    Changes background color
 S    Swaps between full and shaded circle
 D    Changes color (randomly)

These CONSTANTS might be changed: (at own risk, not recommended)
DEVICE                replace with index of another device or leave None for automatic detection of Stereo Mix;
                      change other constants respectively
CIRCLE                change to False for disabling circle mode; swaps also to grayscale volume-based scale
SHADED                changes circle design; works only if CIRCLE == True
nice_colors           list of colors to change with W key
BACKGROUND            None for black
                      True for white
                      False for unstable
SIZE_MULTIPLIER       changes size of the circle
AUTO_SIZE_MULTIPLIER  sets automatically the SIZE_MULTIPLIER
"""
__author__ = "Stepan Talacek"

import sys
from random import choice
import numpy as np
import pyaudio
import pygame
from pynput.keyboard import Controller, Key

# ----- CONSTANTS -----
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
DEVICE = None

CIRCLE = True
SHADED = True
nice_colors = {"purple": (255, 0, 80, 127), "green_aurora": (0, 255, 80, 127), "green": (0, 255, 0)}
CIRCLE_COLOR = nice_colors["green_aurora"]
BACKGROUND = None
SIZE_MULTIPLIER = 3.5
AUTO_SIZE_MULTIPLIER = True

# ----- INITIALIZATION -----
p = pyaudio.PyAudio()

pygame.init()
screen_size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
screen = pygame.display.set_mode(screen_size, flags)
pygame.mouse.set_visible(False)
pygame.display.set_caption("Beat Visualiser")
pygame.display.set_icon(pygame.image.load('icon.png'))

if AUTO_SIZE_MULTIPLIER:
    if pygame.display.Info().current_w < pygame.display.Info().current_h:
        SIZE_MULTIPLIER = pygame.display.Info().current_w // 512
    else:
        SIZE_MULTIPLIER = pygame.display.Info().current_h // 512

keyboard = Controller()

# ----- GET Stereo Mix device -----
for i in range(p.get_device_count()):
    if p.get_device_info_by_index(i)["maxInputChannels"] and "Stereo" in p.get_device_info_by_index(i)["name"]:
        if DEVICE is None:
            DEVICE = p.get_device_info_by_index(i)["index"]
        # print(p.get_device_info_by_index(i))

# ----- OPEN STREAM -----
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                input_device_index=DEVICE,
                frames_per_buffer=CHUNK)

# ----- PROCESS & DISPLAY -----
max_volume_caught = 255
while True:
    data = stream.read(CHUNK)
    converted_data = np.frombuffer(data, dtype=np.int16)
    volume_peak = np.amax(converted_data)
    if volume_peak > max_volume_caught:
        max_volume_caught = volume_peak
        # print(max_volume_caught)

    volume_rv_raw = int(volume_peak * 255 / max_volume_caught)
    volume_rv = volume_rv_raw // 32 * 32

    if not CIRCLE:
        volume_color = [volume_rv] * 3
        screen.fill(volume_color)

    else:
        if not SHADED:
            circle_surface = pygame.surface.Surface(screen_size)
            if BACKGROUND:
                circle_surface.fill([volume_rv] * 3)
            elif BACKGROUND is False:
                circle_surface.fill((255, 255, 255))
            volume_color = [volume_rv if CIRCLE_COLOR[i] <= volume_rv else CIRCLE_COLOR[i] for i in range(3)]
            circle_object = pygame.draw.circle(surface=circle_surface,
                                               color=volume_color,
                                               center=screen.get_rect().center,
                                               radius=int(volume_rv_raw * SIZE_MULTIPLIER),
                                               width=0)
            screen.blit(circle_surface, (0, 0))

        else:
            shade_surface = pygame.surface.Surface(screen_size)
            if BACKGROUND:
                shade_surface.fill([volume_rv] * 3)
            elif BACKGROUND is False:
                shade_surface.fill((255, 255, 255))
            for gradient in range(volume_rv_raw):
                gr_c = [volume_rv_raw - gradient if CIRCLE_COLOR[i] > volume_rv_raw - gradient else CIRCLE_COLOR[i] for
                        i in range(3)]
                pygame.draw.circle(surface=shade_surface,
                                   color=gr_c,
                                   center=screen.get_rect().center,
                                   radius=int(gradient * SIZE_MULTIPLIER),
                                   width=int(2 * SIZE_MULTIPLIER))
            screen.blit(shade_surface, (0, 0))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.mouse.set_visible(True)
            pygame.quit()
            stream.stop_stream()
            stream.close()
            p.terminate()
            sys.exit()
        # RESET max_volume_caught WHENEVER THE VOLUME IS CHANGED TO KEEP RELATIVE SCALE OF volume_rv
        elif event.type == pygame.KEYDOWN and (event.key == 1073741953 or event.key == 1073741952):
            max_volume_caught = 255
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_q):
            keyboard.press(Key.media_previous)
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_e):
            keyboard.press(Key.media_next)
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_d):
            previous_color = CIRCLE_COLOR
            while CIRCLE_COLOR == previous_color:
                CIRCLE_COLOR = choice(list(nice_colors.values()))
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_s):
            SHADED = not SHADED
        elif event.type == pygame.KEYDOWN and (event.key == pygame.K_a):
            if BACKGROUND:
                BACKGROUND = False
            elif BACKGROUND is False:
                BACKGROUND = None
            else:
                BACKGROUND = True
