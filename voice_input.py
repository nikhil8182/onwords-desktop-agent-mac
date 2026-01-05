#!/usr/bin/env python3
"""Voice input for agent"""

import speech_recognition as sr

def listen_for_command(timeout=5):
    """Listen and return spoken text"""
    recognizer = sr.Recognizer()

    print("🎤 Listening... Speak now!")

    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=10)

        text = recognizer.recognize_google(audio)
        print(f"✅ Heard: {text}")
        return text

    except sr.WaitTimeoutError:
        print("⚠️ No speech detected")
        return None
    except sr.UnknownValueError:
        print("⚠️ Could not understand")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


# Test it
if __name__ == "__main__":
    result = listen_for_command()
    if result:
        print(f"You said: {result}")
