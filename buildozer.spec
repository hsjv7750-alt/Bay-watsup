[app]
title = ByWhats
package.name = bywhats
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,ttf
version = 0.1
# قللنا المتطلبات للأساسيات فقط لضمان السرعة
requirements = python3,kivy,arabic-reshaper,python-bidi

orientation = portrait
fullscreen = 0
android.archs = arm64-v8a
android.api = 31
android.minapi = 21
android.skip_update = False
android.accept_sdk_license = True
