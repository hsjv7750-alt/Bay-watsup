import socket, threading, os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.graphics import Color, RoundedRectangle

# --- معالجة اللغة العربية ---
try:
    from arabic_reshaper import reshape
    from bidi.algorithm import get_display
    def fix_arabic(text):
        if not text: return ""
        return get_display(reshape(text))
except Exception:
    def fix_arabic(text): return text[::-1] if text else ""

# تسجيل الخط (تأكد من وجود ملف myfont.ttf في GitHub)
FONT_AVAILABLE = os.path.exists("myfont.ttf")
if FONT_AVAILABLE:
    LabelBase.register(name="ArabicFont", fn_regular="myfont.ttf")
FONT_NAME = "ArabicFont" if FONT_AVAILABLE else "Roboto"

# --- كلاس فقاعة الدردشة ---
class ChatBubble(BoxLayout):
    def __init__(self, text, sender, **kwargs):
        super().__init__(orientation='vertical', size_hint_y=None, padding=(10, 5), **kwargs)
        
        is_me = (sender == "أنا")
        halign = 'right' if is_me else 'left'
        # أخضر واتساب لرسائلي، أبيض للطرف الآخر
        bg_color = (0.85, 0.96, 0.76, 1) if is_me else (1, 1, 1, 1)
        self.pos_hint = {'right': 0.98} if is_me else {'left': 0.02}
        self.size_hint_x = 0.75

        lbl = Label(
            text=fix_arabic(text),
            font_name=FONT_NAME,
            color=(0, 0, 0, 1),
            size_hint_y=None,
            halign=halign,
            valign='middle',
            markup=True
        )
        lbl.bind(width=lambda s, w: s.setter('text_size')(s, (w, None)))
        lbl.bind(texture_size=lambda s, z: s.setter('height')(s, z[1]))
        
        with self.canvas.before:
            Color(*bg_color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[(15, 15), (15, 15), (15, 15), (15, 15)])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        self.add_widget(lbl)
        self.height = lbl.height + 30

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

# --- التطبيق الرئيسي ---
class ByWhatsApp(App):
    def build(self):
        self.conn = None
        self.server_socket = None

        main_layout = BoxLayout(orientation='vertical')
        
        # 1. الشريط العلوي (WhatsApp Header)
        header = BoxLayout(size_hint_y=None, height=65, padding=10)
        with header.canvas.before:
            Color(0.03, 0.33, 0.27, 1) # أخضر واتساب غامق
            self.header_rect = RoundedRectangle(pos=header.pos, size=header.size)
        header.bind(pos=self.update_header, size=self.update_header)
        
        self.title_lbl = Label(text=fix_arabic("ByWhats - متصل"), font_name=FONT_NAME, bold=True, font_size=20)
        header.add_widget(self.title_lbl)
        main_layout.add_widget(header)

        # 2. منطقة الرسائل (خلفية الدردشة)
        chat_bg = BoxLayout(orientation='vertical', padding=10)
        with chat_bg.canvas.before:
            Color(0.9, 0.85, 0.8, 1) # لون خلفية محادثات واتساب
            self.bg_rect = RoundedRectangle(pos=chat_bg.pos, size=chat_bg.size)
        chat_bg.bind(pos=self.update_bg, size=self.update_bg)

        self.scroll = ScrollView()
        self.chat_list = BoxLayout(orientation='vertical', size_hint_y=None, spacing=12)
        self.chat_list.bind(minimum_height=self.chat_list.setter('height'))
        self.scroll.add_widget(self.chat_list)
        chat_bg.add_widget(self.scroll)
        main_layout.add_widget(chat_bg)

        # 3. شريط الإدخال السفلي
        input_area = BoxLayout(size_hint_y=None, height=70, padding=8, spacing=8)
        with input_area.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.in_rect = RoundedRectangle(pos=input_area.pos, size=input_area.size)
        input_area.bind(pos=self.update_in, size=self.update_in)

        self.input_field = TextInput(
            hint_text=fix_arabic("اكتب رسالة..."),
            multiline=False,
            font_name=FONT_NAME,
            size_hint_x=0.75,
            padding=[15, 15],
            background_normal='',
            background_color=(1, 1, 1, 1)
        )
        
        send_btn = Button(
            text=fix_arabic("إرسال"),
            font_name=FONT_NAME,
            size_hint_x=0.25,
            background_normal='',
            background_color=(0.03, 0.33, 0.27, 1),
            color=(1, 1, 1, 1),
            bold=True
        )
        send_btn.bind(on_release=self.send_message)
        
        input_area.add_widget(self.input_field)
        input_area.add_widget(send_btn)
        main_layout.add_widget(input_area)

        # تشغيل السيرفر في الخلفية
        threading.Thread(target=self.start_server, daemon=True).start()
        
        return main_layout

    def update_header(self, instance, value): self.header_rect.pos = instance.pos; self.header_rect.size = instance.size
    def update_bg(self, instance, value): self.bg_rect.pos = instance.pos; self.bg_rect.size = instance.size
    def update_in(self, instance, value): self.in_rect.pos = instance.pos; self.in_rect.size = instance.size

    def update_log(self, sender, message):
        bubble = ChatBubble(text=message, sender=sender)
        self.chat_list.add_widget(bubble)
        Clock.schedule_once(lambda dt: setattr(self.scroll, 'scroll_y', 0))

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', 12345))
            self.server_socket.listen(5)
            while True:
                conn, addr = self.server_socket.accept()
                self.conn = conn
                threading.Thread(target=self.receive_messages, args=(conn,), daemon=True).start()
        except: pass

    def receive_messages(self, conn):
        while True:
            try:
                data = conn.recv(1024).decode('utf-8')
                if data:
                    Clock.schedule_once(lambda dt: self.update_log("الطرف الآخر", data))
            except: break

    def send_message(self, *args):
        msg = self.input_field.text.strip()
        if msg:
            if self.conn:
                try:
                    self.conn.send(msg.encode('utf-8'))
                    self.update_log("أنا", msg)
                    self.input_field.text = ""
                except: self.update_log("نظام", "فشل الإرسال")
            else:
                # محاولة الاتصال كـ كليينت إذا لم نكن سيرفر
                threading.Thread(target=self.connect_to_peer, args=(msg,), daemon=True).start()

    def connect_to_peer(self, msg):
        # محاولة الاتصال بالآي بي الافتراضي للهوتسبوت
        try:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(('192.168.43.1', 12345))
            self.conn = client_sock
            self.conn.send(msg.encode('utf-8'))
            Clock.schedule_once(lambda dt: self.update_log("أنا", msg))
            Clock.schedule_once(lambda dt: setattr(self.input_field, 'text', ''))
            threading.Thread(target=self.receive_messages, args=(self.conn,), daemon=True).start()
        except:
            Clock.schedule_once(lambda dt: self.update_log("نظام", "لا يوجد طرف آخر متصل بالشبكة"))

if __name__ == '__main__':
    ByWhatsApp().run()

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
