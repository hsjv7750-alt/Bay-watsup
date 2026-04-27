# ByWhats — تطبيق دردشة محلي عبر الهوتسبوت

تطبيق Kivy لأندرويد يتيح الدردشة بين جهازين عبر شبكة Wi-Fi محلية (هوتسبوت) بدون إنترنت.

## الملفات

- `main.py` — كود التطبيق الرئيسي (Kivy + Sockets + معالجة العربية).
- `buildozer.spec` — إعدادات بناء APK.
- `.github/workflows/main.yml` — أتمتة بناء الـ APK على GitHub Actions.
- `myfont.ttf` — **يجب عليك إرفاقه يدوياً** (أي خط TTF يدعم العربية، مثل Amiri أو Cairo أو NotoNaskhArabic).

## مهم جداً: ملف الخط

قبل رفع المشروع إلى GitHub، أضف ملف خط عربي باسم `myfont.ttf` بجانب `main.py`.

أمثلة لخطوط مجانية تدعم العربية:
- [Amiri](https://fonts.google.com/specimen/Amiri)
- [Cairo](https://fonts.google.com/specimen/Cairo)
- [Noto Naskh Arabic](https://fonts.google.com/noto/specimen/Noto+Naskh+Arabic)

نزّل الخط، وأعد تسميته إلى `myfont.ttf`، وضعه في نفس مجلد `main.py`.

## خطوات الاستخدام

1. أنشئ مستودع GitHub جديد.
2. ارفع كل محتويات هذا المجلد (بما فيها `myfont.ttf`).
3. ادخل تبويب **Actions** في المستودع وانتظر انتهاء البناء (10-30 دقيقة في أول مرة).
4. حمّل ملف الـ APK من قسم **Artifacts** في صفحة الـ workflow.

## كيف يعمل التطبيق

- الجهاز الأول يفتح هوتسبوت ويضغط **HOST**.
- يأخذ الـ IP المعروض في أعلى الشاشة ويعطيه للصديق.
- الجهاز الثاني يكتب الـ IP في خانة الكتابة ويضغط **JOIN**.
- بعد الاتصال، يكتب أي رسالة ويضغط **SEND**.
- لإرسال صورة، اكتب مسار الصورة الكامل واضغط **IMG**.
