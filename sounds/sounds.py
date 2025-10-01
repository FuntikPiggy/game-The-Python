import os
import sys
import pygame as pg


try:
   wd = sys._MEIPASS
except AttributeError:
   wd = os.getcwd()
file_path = os.path.join(wd,)

pg.init()


def play_music():
    """Выполняет включение/отключение музыки."""
    global is_playing
    global is_prodigy
    if is_playing:
        pg.mixer.music.stop()
        is_prodigy = False
        pg.mixer.music.load(music_list[is_prodigy])
    else:
        pg.mixer.music.play()
    is_playing = not is_playing


def prodigy():
    """Пасхалочка - смена музыкальной композиции."""
    global is_prodigy
    if is_playing:
        play_music()
    is_prodigy = True
    pg.mixer.music.load(music_list[is_prodigy])
    play_music()


def play_sound(sound):
    """Воспроизводит звуковой эффект."""
    sounds_dict[sound].play()


pg.mixer.music.load(os.path.join(wd, 'sounds', 'music_01.mid'))
pg.mixer.music.set_volume(0.1)
pg.mixer.music.play(-1)
is_playing = True
is_prodigy = False

pg.mixer.init()
step_sound1 = pg.mixer.Sound(os.path.join(wd, 'sounds', 'step_01.mp3'))
step_sound2 = pg.mixer.Sound(os.path.join(wd, 'sounds', 'step_04.mp3'))
eat_sound = pg.mixer.Sound(os.path.join(wd, 'sounds', 'eating_01.mp3'))
btn_click_sound = pg.mixer.Sound(os.path.join(wd, 'sounds', 'btn_01.mp3'))
btn_hover_sound = pg.mixer.Sound(os.path.join(wd, 'sounds', 'btn_02.mp3'))
crash_sound = pg.mixer.Sound(os.path.join(wd, 'sounds', 'crash_02.mp3'))
ta_dam_sound = pg.mixer.Sound(os.path.join(wd, 'sounds', 'ta-dam_01.mp3'))
cut_sound = pg.mixer.Sound(os.path.join(wd, 'sounds', 'cut_02.mp3'))
step_sound1.set_volume(0.1)
step_sound2.set_volume(0.1)
eat_sound.set_volume(0.3)
btn_hover_sound.set_volume(0.2)
crash_sound.set_volume(0.7)
ta_dam_sound.set_volume(0.8)
cut_sound.set_volume(0.1)

sounds_dict = {
    'step1': step_sound1,
    'step2': step_sound2,
    'eat': eat_sound,
    'click': btn_click_sound,
    'hover': btn_hover_sound,
    'crash': crash_sound,
    'ta_dam': ta_dam_sound,
    'cut': cut_sound,
}
music_list = [os.path.join(wd, 'sounds', 'music_01.mid'),
              os.path.join(wd, 'sounds', 'Prodigy.mid')]
