[app]
title = JarvisAssistant
package.name = jarvis
package.domain = org.example
source.dir = .
source.include_exts = py,json
version = 1.0
requirements = python3,kivy,pyttsx3,speechrecognition,dateparser
orientation = portrait
android.permissions = RECORD_AUDIO,INTERNET
android.minapi = 21
android.api = 33
android.ndk = 23b

[buildozer]
log_level = 2
warn_on_root = 1
