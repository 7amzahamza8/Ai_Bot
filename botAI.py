import asyncio
import os
import re
import tempfile
import threading

import edge_tts
import pygame
import requests
import sounddevice as sd
from faster_whisper import WhisperModel

import math_solver
import translator
from sound import trigger_sound

MODEL_NAME = "llama3.2:3b"
SAMPLE_RATE = 16000
SECONDS = 5
MAX_CONVERSATION = 20      # آخر كام رسالة نبعتهم لـ Ollama (غير رسالة النظام). من غير حد المحادثة بتكبر لحد ما الموديل يتلخبط

print("Loading speech recognition model...")
# من غير language=... عشان Whisper يعرف اللغة لوحده (عربي / إنجليزي / ألماني)
speech_model = WhisperModel("base", device="cpu", compute_type="int8")

conversation = [
    {
        "role": "system",
        "content": (
            "You are a helpful robot assistant. "
            "Respond concisely and naturally in the language spoken to you."
        ),
    }
]

robot_thread = None
stop_event = threading.Event()

VOICES = {
    "en": "en-US-SteffanNeural",
    "de": "de-DE-KillianNeural",
    "ar": "ar-EG-SalmaNeural",
}


# ---------------------------------------------------------------
# الكلام (edge-tts محتاج إنترنت)
# ---------------------------------------------------------------
def _pick_voice(text, lang):
    if lang in VOICES:
        return VOICES[lang]
    if any("؀" <= c <= "ۿ" for c in text):     # نص عربي
        return VOICES["ar"]
    return VOICES["en"]


def speak(text, lang=None):
    """lang = "en" / "de" / "ar". لو سبته فاضي: عربي بيتعرف من الحروف، والباقي إنجليزي.
    ترجمة لألماني لازم تعدّي lang="de" وإلا هتتقرأ بصوت إنجليزي."""
    print("Robot:", text)
    if not text or not text.strip():
        return

    voice = _pick_voice(text, lang)

    async def _generate(path):
        await edge_tts.Communicate(text, voice).save(path)

    # اسم ملف مؤقت مختلف كل مرة، عشان محدش يمسح أو يقفل ملف التاني
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        asyncio.run(_generate(path))
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if stop_event.is_set():
                pygame.mixer.music.stop()
                break
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()
    except Exception as error:
        print("TTS Error:", error)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ---------------------------------------------------------------
# السمع والمخ
# ---------------------------------------------------------------
def listen(duration=SECONDS):
    print("Listening...")
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )

    # بنستنى على دفعات صغيرة عشان "stop" توقف التسجيل فوراً
    for _ in range(int(duration * 10)):
        if stop_event.is_set():
            sd.stop()
            return ""
        sd.sleep(100)
    sd.wait()

    segments, _ = speech_model.transcribe(
        audio.flatten(),
        vad_filter=True,
        beam_size=5,
        condition_on_previous_text=False,
    )
    return " ".join(segment.text for segment in segments).strip()


def ask_robot(text):
    conversation.append({"role": "user", "content": text})
    del conversation[1:-MAX_CONVERSATION]
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": MODEL_NAME, "messages": conversation, "stream": False},
            timeout=180,
        )
        response.raise_for_status()
        answer = response.json()["message"]["content"]
    except Exception as error:
        print("Ollama connection error:", error)
        conversation.pop()      # السؤال ماتجاوبش: نشيله عشان ماييجيش سؤالين ورا بعض في المحادثة
        return "I can't reach my brain right now."
    conversation.append({"role": "assistant", "content": answer})
    return answer


# ---------------------------------------------------------------
# الأوامر الصوتية: رياضيات / مسح السجل / ترجمة
# كل واحدة بترجّع True لو هي اللي اتعاملت مع الجملة
# ---------------------------------------------------------------
# "solve x^2 - 4" أو "احسب 2+3" أو "حل x+1=3" لازم تبدأ بالكلمة.
# (قبل كده كان بيدوّر عليها جوه الجملة، فـ "resolve this" كانت بتتفهم "solve")
SOLVE_COMMAND = re.compile(r"^\W*(?:solve|احسب|حل)\s+(.+)$", re.IGNORECASE | re.DOTALL)


def handle_math(user_text):
    match = SOLVE_COMMAND.match(user_text)
    if not match:
        return False
    try:
        result = math_solver.solve(match.group(1).strip(), "solve")
    except math_solver.MathError as error:
        speak(error.text("en"), lang="en")
    else:
        if result["kind"] == "no_solution":
            speak("There is no solution.", lang="en")
        else:
            speak(f"The result is {result['result']}", lang="en")
    return True


def handle_clear(user_text):
    text = user_text.lower()
    if "clear history" in text or "امسح السجل" in user_text:
        math_solver.clear_history()
        del conversation[1:]
        speak("History cleared successfully.", lang="en")
        return True
    return False


def handle_translation(user_text):
    """"translate to German: good morning" (نفس صيغ الـ API). بيتكلم بصوت اللغة المترجم ليها."""
    parsed = translator.parse_command(user_text)
    if parsed is None:
        return False
    target, text = parsed

    if not text:
        speak("What should I translate?", lang="en")
        text = listen()
        if not text:
            return True
        print("You:", text)

    try:
        # source="auto": Whisper بيتعرف على أي لغة، فمنفترضش إنها إنجليزي
        result = translator.translate(text, target, source="auto")
    except translator.TranslateError as error:
        speak(error.text("en"), lang="en")
    except translator.TranslatorUnavailable:
        speak("I can't reach my translator. Is Ollama running?", lang="en")
    else:
        speak(result["translation"], lang=target)
    return True


def handle_voice_commands(user_text):
    # الترجمة الأول: "hi" جوه جملة ترجمة ماتشغّلش الصوت بالغلط
    return handle_translation(user_text) or handle_math(user_text) or handle_clear(user_text)


def robot_loop():
    speak("Hello! How can I help you?", lang="en")

    while not stop_event.is_set():
        try:
            user_text = listen()
            if not user_text:
                continue

            print("You:", user_text)

            if handle_voice_commands(user_text):
                continue

            if trigger_sound(user_text):
                continue

            if "stop robot" in user_text.lower() or "توقف" in user_text:
                speak("Okay, shutting down now.", lang="en")
                break

            speak(ask_robot(user_text))

        except Exception as error:
            print("Loop error:", error)
            sd.sleep(1000)

    print("Robot stopped.")


def start_robot():
    """if the robot is not already running, start it in a new thread and return True. Otherwise, return False."""
    global robot_thread
    if robot_thread and robot_thread.is_alive():
        return False

    stop_event.clear()
    del conversation[1:]
    robot_thread = threading.Thread(target=robot_loop, daemon=True)
    robot_thread.start()
    return True


def stop_robot():
    stop_event.set()
