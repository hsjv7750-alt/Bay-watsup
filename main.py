import socket, threading, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.text import LabelBase

try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    def fix_arabic(text):
        if not text:
            return ""
        return get_display(reshape(text))
except Exception:
    def fix_arabic(text):
        return text[::-1] if text else ""

FONT_AVAILABLE = os.path.exists("myfont.ttf")
if FONT_AVAILABLE:
    LabelBase.register(name="ArabicFont", fn_regular="myfont.ttf")

FONT_NAME = "ArabicFont" if FONT_AVAILABLE else "Roboto"


class ByWhatsApp(App):
    title = "ByWhats"

    def build(self):
        self.conn = None
        self.server_socket = None

        root = BoxLayout(orientation='vertical', padding=10, spacing=8)

        self.ip_info = Label(
            text=fix_arabic("جاري فحص الشبكة..."),
            size_hint_y=None,
            height=40,
            font_name=FONT_NAME,
            color=(1, 1, 0, 1),
            halign='center',
        )
        root.add_widget(self.ip_info)
        self.show_my_ip()

        self.scroll = ScrollView(size_hint=(1, 1))
        self.chat_log = Label(
            text=fix_arabic("-- بداية الدردشة --"),
            size_hint_y=None,
            halign='right',
            valign='top',
            font_name=FONT_NAME,
            markup=True,
            text_size=(None, None),
            padding=(10, 10),
        )
        self.chat_log.bind(texture_size=self._update_log_size)
        self.scroll.add_widget(self.chat_log)
        root.add_widget(self.scroll)

        self.input_field = TextInput(
            hint_text="Enter IP for JOIN / or Message for SEND",
            multiline=False,
            size_hint_y=None,
            height=50,
            font_name=FONT_NAME,
        )
        root.add_widget(self.input_field)

        btns = BoxLayout(size_hint_y=None, height=55, spacing=5)
        btns.add_widget(Button(text="HOST", on_release=self.start_host, background_color=(0.2, 0.6, 1, 1)))
        btns.add_widget(Button(text="JOIN", on_release=self.start_client, background_color=(0.2, 0.8, 0.4, 1)))
        btns.add_widget(Button(text="SEND", on_release=self.send_msg, background_color=(1, 0.5, 0.2, 1)))
        btns.add_widget(Button(text="IMG", on_release=self.send_image, background_color=(0.7, 0.3, 0.9, 1)))
        root.add_widget(btns)

        return root

    def _update_log_size(self, instance, value):
        instance.size = value
        instance.text_size = (self.scroll.width - 20, None)

    def show_my_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(2)
            s.connect(("8.8.8.8", 80))
            my_ip = s.getsockname()[0]
            self.ip_info.text = fix_arabic(f"عنوانك (IP) هو: {my_ip}")
            s.close()
        except Exception:
            try:
                hostname = socket.gethostname()
                my_ip = socket.gethostbyname(hostname)
                self.ip_info.text = fix_arabic(f"عنوانك (IP) هو: {my_ip}")
            except Exception:
                self.ip_info.text = fix_arabic("يرجى فتح الهوتسبوت أولاً")

    def update_log(self, sender, msg, color="ffffff"):
        try:
            txt = f"[color={color}][b]{fix_arabic(sender)}[/b]: {fix_arabic(msg)}[/color]"
            Clock.schedule_once(lambda dt: setattr(
                self.chat_log, 'text', self.chat_log.text + "\n" + txt
            ))
        except Exception:
            pass

    def start_host(self, *args):
        threading.Thread(target=self.host_logic, daemon=True).start()

    def host_logic(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", 5555))
            self.server_socket.listen(1)
            self.update_log("نظام", "أنت المستضيف.. بانتظار الصديق", "ffff00")
            self.conn, addr = self.server_socket.accept()
            self.update_log("نظام", f"تم الاتصال مع: {addr[0]}", "00ff00")
            self.receive_loop()
        except Exception as e:
            self.update_log("نظام", f"خطأ في الاستضافة: {str(e)}", "ff0000")

    def start_client(self, *args):
        ip = (self.input_field.text or "192.168.43.1").strip()
        threading.Thread(target=self.client_logic, args=(ip,), daemon=True).start()

    def client_logic(self, ip):
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.settimeout(10)
            self.conn.connect((ip, 5555))
            self.conn.settimeout(None)
            self.update_log("نظام", "تم الاتصال بنجاح!", "00ff00")
            Clock.schedule_once(lambda dt: setattr(self.input_field, 'text', ''))
            self.receive_loop()
        except Exception:
            self.update_log("نظام", "فشل الاتصال بالآدمن.. تأكد من الـ IP", "ff0000")

    def receive_loop(self):
        while True:
            try:
                data = self.conn.recv(4096)
                if not data:
                    break
                try:
                    text = data.decode('utf-8')
                except UnicodeDecodeError:
                    text = "[بيانات غير نصية]"
                if text.startswith("[IMG]"):
                    self.update_log("صديقك", f"أرسل صورة: {text[5:]}", "ff66cc")
                else:
                    self.update_log("صديقك", text, "ffffff")
            except Exception:
                self.update_log("نظام", "انقطع الاتصال", "ff0000")
                break

    def send_msg(self, *args):
        msg = self.input_field.text.strip()
        if not msg:
            return
        if not self.conn:
            self.update_log("نظام", "لا يوجد اتصال نشط", "ff0000")
            return
        try:
            self.conn.send(msg.encode('utf-8'))
            self.update_log("أنا", msg, "00ffff")
            Clock.schedule_once(lambda dt: setattr(self.input_field, 'text', ''))
        except Exception:
            self.update_log("نظام", "فشل الإرسال", "ff0000")

    def send_image(self, *args):
        path = self.input_field.text.strip()
        if not path:
            self.update_log("نظام", "ضع مسار الصورة في خانة الكتابة", "ffaa00")
            return
        if not os.path.exists(path):
            self.update_log("نظام", "الملف غير موجود", "ff0000")
            return
        if not self.conn:
            self.update_log("نظام", "لا يوجد اتصال نشط", "ff0000")
            return
        try:
            note = f"[IMG]{os.path.basename(path)}"
            self.conn.send(note.encode('utf-8'))
            self.update_log("أنا", f"أرسلت صورة: {os.path.basename(path)}", "ff66cc")
            Clock.schedule_once(lambda dt: setattr(self.input_field, 'text', ''))
        except Exception:
            self.update_log("نظام", "فشل إرسال الصورة", "ff0000")

    def on_stop(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        try:
            if self.server_socket:
                self.server_socket.close()
        except Exception:
            pass


if __name__ == "__main__":
    ByWhatsApp().run()
