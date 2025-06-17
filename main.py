from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
import json, os, re, difflib
from datetime import datetime
import dateparser
import threading
import speech_recognition as sr
import pyttsx3

Window.size = (360, 640)

REMINDER_FILE = "reminders.json"

recognizer = sr.Recognizer()
engine = pyttsx3.init()
engine.setProperty("voice", engine.getProperty("voices")[0].id)

class JarvisGUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.output = Label(size_hint_y=None, text_size=(Window.width - 20, None))
        self.output.bind(texture_size=self.update_label_height)

        self.scroll = ScrollView(size_hint=(1, 0.85))
        self.scroll.add_widget(self.output)

        self.button = Button(text="🎙️ Talk to Jarvis", size_hint=(1, 0.15), on_press=self.start_jarvis)

        self.add_widget(self.scroll)
        self.add_widget(self.button)

    def update_label_height(self, instance, size):
        self.output.height = size[1]

    @mainthread
    def add_message(self, msg, sender="Jarvis"):
        self.output.text += f"[b]{sender}:[/b] {msg}\n\n"

    def speak(self, text):
        self.add_message(text, "Jarvis")
        engine.say(text)
        engine.runAndWait()

    def listen(self, prompt=None):
        if prompt:
            self.speak(prompt)
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source, timeout=8)
                command = recognizer.recognize_google(audio).lower()
                self.add_message(command, "You")
                return command
            except Exception:
                self.speak("Sorry, I didn't catch that.")
                return ""

    def parse_datetime_input(self, text):
        time_pattern = r"\b\d{1,2}(:\d{2})?\s*(am|pm)?\b"
        date_keywords = [
            r"today", r"tomorrow", r"day after tomorrow", r"in \d+ (days?|weeks?|months?)",
            r"next (monday|tuesday|wednesday|thursday|friday|saturday|sunday|week|month)",
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}"
        ]
        has_time = re.search(time_pattern, text)
        has_date = re.search("|".join(date_keywords), text, re.IGNORECASE)
        if has_date and has_time:
            return "both"
        elif has_date:
            return "date"
        elif has_time:
            return "time"
        else:
            return "none"

    def load_reminders(self):
        return json.load(open(REMINDER_FILE)) if os.path.exists(REMINDER_FILE) else {}

    def save_reminders(self, data):
        with open(REMINDER_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def add_reminder(self):
        content = self.listen("What is the reminder about?")
        if not content:
            return
        reminder_info = {"content": content}

        while True:
            date_input = self.listen("Say the date and time like 'tomorrow at 9 AM'")
            if not date_input:
                continue
            dt_type = self.parse_datetime_input(date_input)
            if dt_type == "none":
                self.speak("Try again.")
                continue
            elif dt_type == "date":
                time_part = self.listen("Say the time.")
                if time_part:
                    date_input += " " + time_part
            elif dt_type == "time":
                date_part = self.listen("Say the date.")
                if date_part:
                    date_input = date_part + " " + date_input

            dt = dateparser.parse(date_input, settings={"PREFER_DATES_FROM": "future"})
            if dt and dt > datetime.now():
                break
            self.speak("Invalid or past time. Try again.")

        reminder_info["datetime"] = dt.strftime("%Y-%m-%d %H:%M")

        for _ in range(3):
            freq = self.listen("Repeat: daily, weekly, monthly or once?")
            matched = difflib.get_close_matches(freq, ["daily", "weekly", "monthly", "once"], n=1, cutoff=0.6)
            if matched:
                reminder_info["repeat"] = matched[0]
                break
            self.speak("I didn't get that.")

        confirm = self.listen(f"Save reminder '{reminder_info['content']}' on {reminder_info['datetime']}?")
        if "yes" in confirm or "do it" in confirm:
            reminders = self.load_reminders()
            reminders[reminder_info["datetime"]] = reminder_info
            self.save_reminders(reminders)
            self.speak("Reminder saved.")
        else:
            self.speak("Reminder not saved.")

    def view_reminders(self):
        reminders = self.load_reminders()
        if not reminders:
            self.speak("No reminders found.")
            return
        for dt_str, info in reminders.items():
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            msg = f"{info['content']} at {dt.strftime('%b %d %I:%M %p')} ({info.get('repeat', 'once')})"
            self.speak(msg)

    def remove_reminder(self):
        target = self.listen("What reminder to remove?")
        reminders = self.load_reminders()
        for k in list(reminders):
            if target in reminders[k]["content"].lower():
                confirm = self.listen(f"Remove {reminders[k]['content']}?")
                if "yes" in confirm:
                    del reminders[k]
                    self.save_reminders(reminders)
                    self.speak("Reminder removed.")
                    return
        self.speak("No matching reminder.")

    def start_jarvis(self, instance):
        def task():
            self.speak("Hello! I'm Jarvis.")
            while True:
                command = self.listen("Your command?")
                if "add" in command:
                    self.add_reminder()
                elif "view" in command:
                    self.view_reminders()
                elif "remove" in command:
                    self.remove_reminder()
                elif "exit" in command or "stop" in command:
                    self.speak("Goodbye!")
                    break
                else:
                    self.speak("Unknown command.")
        threading.Thread(target=task).start()

class JarvisApp(App):
    def build(self):
        return JarvisGUI()

if __name__ == "__main__":
    JarvisApp().run()
