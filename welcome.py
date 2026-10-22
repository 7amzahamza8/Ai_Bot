import os
import time

import pygame
from gtts import gTTS

AUDIO_INTRO = "intro_full.mp3"
AUDIO_SHORT = "welcome_short.mp3"


def create_audio_if_missing(text: str, filename: str, lang: str = 'ar'):
    if not os.path.exists(filename):
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)


def play_and_delete_if_needed(file_path: str, delete_after: bool = False):
    if not os.path.exists(file_path):
        return False

    # لو الـ mixer شغال أصلاً (الروبوت أو الأصوات بتستخدمه)، ماننهيهوش بعد ما نخلّص:
    # pygame.mixer.quit() كان بيقفله على باقي البرنامج.
    we_started_mixer = not pygame.mixer.get_init()
    try:
        if we_started_mixer:
            pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except Exception as error:
        print("Welcome audio error:", error)    # قبل كده الخطأ كان بيختفي من غير أي رسالة
        return False
    finally:
        if we_started_mixer and pygame.mixer.get_init():
            pygame.mixer.quit()

    if delete_after and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError as error:
            print("Could not delete", file_path, "-", error)
    return True


def welcome():
    if os.path.exists(AUDIO_INTRO):
        play_and_delete_if_needed(AUDIO_INTRO, delete_after=True)
    else:
        play_and_delete_if_needed(AUDIO_SHORT, delete_after=False)


if __name__ == "__main__":
    welcome()
