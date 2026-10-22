import re
import threading
from pathlib import Path

import pygame

BASE_DIR = Path(__file__).resolve().parent
# ملف الصوت: gTTS.py بيحفظ "Sound_1.mp3"، وكان فيه نسخ بتدوّر على "Sound.mp3". بندوّر على الاتنين،
# جنب الملف الأول ثم في الفولدر اللي شغّلت منه.
AUDIO_NAMES = ("Sound_1.mp3", "Sound.mp3")

# هنا بتحدد نقطة البداية والنهاية (بالثواني) لكل كلمة.
# الحروف الكبيرة والصغيرة مش فارقة: "Hamza" و "hamza" نفس الكلمة.
# ترتيب الكلمات هنا هو ترتيب الأزرار في الصفحة (الأرقام 1 و 2 و 3).
WORDS = {
    "Hamza": (0, 4),
    "Ahmed": (4, 8),
    "hi": (12, 15),
}

stop_timer = None
_lock = threading.Lock()


def _audio_path():
    for folder in (BASE_DIR, Path.cwd()):
        for name in AUDIO_NAMES:
            path = folder / name
            if path.is_file():
                return path
    return None


def _key(word):
    """بيرجّع كتابة الكلمة زي ما هي في WORDS بغض النظر عن حالة الحروف، أو None."""
    word = (word or "").strip().lower()
    for name in WORDS:
        if name.lower() == word:
            return name
    return None


def find_sound(word):
    key = _key(word)
    return WORDS[key] if key else None


def list_sounds():
    """الصفحة بتقرا الكلمات ومدتها من هنا (route /sounds)، فمفيش قايمة تانية تعدّلها."""
    return [
        {"word": name, "start": start, "end": end, "duration": end - start}
        for name, (start, end) in WORDS.items()
    ]


def play_word(word):
    """بيشغّل المقطع. بيرجّع False لو الملف مش موجود أو مفيش كارت صوت (بدل ما يوقّع الخيط)."""
    global stop_timer
    key = _key(word)
    if key is None:
        return False
    path = _audio_path()
    if path is None:
        print(f"Cannot play '{key}': none of {AUDIO_NAMES} was found next to sound.py or in the working directory.")
        return False
    start, end = WORDS[key]
    with _lock:
        try:
            if not pygame.mixer.get_init():      # welcome.py أو الكلام ممكن يكون قفل الـ mixer
                pygame.mixer.init()
            # التحميل كل مرة: صوت الروبوت (edge-tts) بيستخدم نفس pygame.mixer.music وبيفرّغه بعد ما يخلص
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play(start=start)
        except pygame.error as error:
            print("Audio error:", error)
            return False
        if stop_timer:
            stop_timer.cancel()
        stop_timer = threading.Timer(end - start, _stop)
        stop_timer.daemon = True
        stop_timer.start()
    return True


def _stop():
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
    except pygame.error:
        pass


def trigger_sound(text):
    text = (text or "").lower()
    for word in WORDS:
        # كلمة كاملة بس: "hi" ماتشغّلش الصوت جوه "this" أو "which"
        if re.search(rf"\b{re.escape(word.lower())}\b", text) and play_word(word):
            return True
    return False
