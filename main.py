import sqlite3
import random
import time
import datetime
import os
import shutil
import webbrowser
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
from kivy.uix.checkbox import CheckBox
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock

# --- DEVELOPER CONFIGURATION ---
DEVELOPER_EMAIL = "betafrica3@gmail.com"  
ECOCASH_NAME = "Campus Hub Developer"

# Initialize SQLite Database & Directories
def init_db():
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    conn = sqlite3.connect('campus_app.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            surname TEXT,
            dob TEXT,
            gender TEXT,
            username TEXT,
            password TEXT,
            phone TEXT,
            university TEXT,
            location TEXT,
            bio TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_text TEXT,
            post_type TEXT,
            media_path TEXT,
            price TEXT,
            seller_username TEXT,
            seller_ecocash TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            buyer_username TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            feedback_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cursor.execute('INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)', ('ecocash_number', '0777907187'))
    conn.commit()
    conn.close()

temp_user_data = {}
generated_code = ""
code_expiry_time = 0
active_username = ""

def set_background(instance, color):
    with instance.canvas.before:
        Color(*color)
        instance.rect = RoundedRectangle(size=instance.size, pos=instance.pos, radius=[12])
    instance.bind(
        size=lambda s, val: setattr(instance.rect, 'size', val),
        pos=lambda s, val: setattr(instance.rect, 'pos', val)
    )

# --- WELCOME SCREEN ---
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super(WelcomeScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        set_background(layout, (0.11, 0.13, 0.19, 1))
        
        avatar_container = BoxLayout(size_hint=(None, None), size=(100, 100), pos_hint={'center_x': 0.5})
        with avatar_container.canvas.before:
            Color(0.18, 0.70, 0.44, 1)
            self.avatar_circle = Ellipse(size=(100, 100), pos=avatar_container.pos)
        avatar_container.bind(pos=lambda s, p: setattr(self.avatar_circle, 'pos', p))
        
        avatar_label = Label(text='U', font_size=36, bold=True, halign='center', valign='middle', color=(1, 1, 1, 1))
        avatar_label.bind(size=avatar_label.setter('text_size'))
        avatar_container.add_widget(avatar_label)
        layout.add_widget(avatar_container)
        
        layout.add_widget(Label(text='[b]Welcome to Campus Hub[/b]', markup=True, font_size=24, size_hint_y=None, height=45, color=(0.9, 0.9, 0.9, 1), halign='center'))
        layout.add_widget(Label(text='Your student marketplace, study network, and social stream.', font_size=14, size_hint_y=None, height=35, color=(0.7, 0.7, 0.7, 1), halign='center'))
        
        signin_btn = Button(text='Sign In 🔑', size_hint_y=None, height=55, background_color=(0.12, 0.53, 0.90, 1), bold=True)
        signin_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'signin'))
        layout.add_widget(signin_btn)
        
        register_btn = Button(text='Create Account (Register) ➡', size_hint_y=None, height=55, background_color=(0.18, 0.70, 0.44, 1), bold=True)
        register_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'reg_step1'))
        layout.add_widget(register_btn)
        
        self.add_widget(layout)


# --- SIGN IN SCREEN ---
class SignInScreen(Screen):
    def __init__(self, **kwargs):
        super(SignInScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15)
        set_background(layout, (0.11, 0.13, 0.19, 1))
        
        layout.add_widget(Label(text='[b]Sign In to Campus Hub[/b]', markup=True, font_size=22, size_hint_y=None, height=45, color=(0.9, 0.9, 0.9, 1), halign='center'))
        
        self.error_label = Label(text='', font_size=14, size_hint_y=None, height=25, color=(0.9, 0.4, 0.4, 1), halign='center')
        self.error_label.bind(size=self.error_label.setter('text_size'))
        
        self.username_input = TextInput(hint_text='Username (e.g. @student)', multiline=False, size_hint_y=None, height=50)
        self.password_input = TextInput(hint_text='Password', password=True, multiline=False, size_hint_y=None, height=50)
        
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(self.error_label)
        
        login_btn = Button(text='Login 🚀', size_hint_y=None, height=55, background_color=(0.18, 0.70, 0.44, 1), bold=True)
        login_btn.bind(on_press=self.process_login)
        layout.add_widget(login_btn)
        
        back_btn = Button(text='⬅ Back to Welcome', size_hint_y=None, height=45, background_color=(0.4, 0.4, 0.4, 1), bold=True)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'welcome'))
        layout.add_widget(back_btn)
        
        self.add_widget(layout)

    def process_login(self, instance):
        global active_username
        uname = self.username_input.text.strip()
        pwd = self.password_input.text.strip()
        
        if not uname or not pwd:
            self.error_label.text = "❌ Username and Password cannot be blank."
            return
            
        conn = sqlite3.connect('campus_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, password FROM users WHERE username = ?', (uname,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[1] == pwd:
            active_username = row[0]
            self.error_label.text = ""
            self.username_input.text = ""
            self.password_input.text = ""
            self.manager.current = 'main_dashboard'
        else:
            self.error_label.text = "❌ Invalid username or password."


# --- STEP 1: Name ---
class RegStep1(Screen):
    def __init__(self, **kwargs):
        super(RegStep1, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15)
        set_background(layout, (0.11, 0.13, 0.19, 1))
        
        layout.add_widget(Label(text='[b]Step 1 of 4: First Name[/b]', markup=True, font_size=20, size_hint_y=None, height=40, color=(0.9, 0.9, 0.9, 1)))
        
        self.error_label = Label(text='', font_size=14, size_hint_y=None, height=25, color=(0.9, 0.4, 0.4, 1), halign='center')
        self.error_label.bind(size=self.error_label.setter('text_size'))
        
        self.name_input = TextInput(hint_text='Enter your First Name...', multiline=False, size_hint_y=None, height=50)
        layout.add_widget(self.name_input)
        layout.add_widget(self.error_label)
        
        btn_layout = GridLayout(cols=2, size_hint_y=None, height=55, spacing=15)
        back_btn = Button(text='⬅ Back', background_color=(0.4, 0.4, 0.4, 1), bold=True)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'welcome'))
        next_btn = Button(text='Next Step ➡', background_color=(0.12, 0.53, 0.90, 1), bold=True)
        next_btn.bind(on_press=self.go_to_next)
        
        btn_layout.add_widget(back_btn)
        btn_layout.add_widget(next_btn)
        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def go_to_next(self, instance):
        global temp_user_data
        name = self.name_input.text.strip()
        if not name:
            self.error_label.text = "❌ First name cannot be left blank."
            return
        self.error_label.text = ""
        temp_user_data['name'] = name
        self.manager.current = 'reg_step2'


# --- STEP 2: Personal Details ---
class RegStep2(Screen):
    def __init__(self, **kwargs):
        super(RegStep2, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15)
        set_background(layout, (0.11, 0.13, 0.19, 1))
        
        layout.add_widget(Label(text='[b]Step 2 of 4: Personal Details[/b]', markup=True, font_size=20, size_hint_y=None, height=40, color=(0.9, 0.9, 0.9, 1)))
        
        self.error_label = Label(text='', font_size=14, size_hint_y=None, height=25, color=(0.9, 0.4, 0.4, 1), halign='center')
        self.error_label.bind(size=self.error_label.setter('text_size'))
        
        self.surname_input = TextInput(hint_text='Surname', multiline=False, size_hint_y=None, height=50)
        self.dob_input = TextInput(hint_text='Date of Birth (YYYY-MM-DD)', multiline=False, size_hint_y=None, height=50)
        self.gender_input = TextInput(hint_text='Gender (Male or Female)', multiline=False, size_hint_y=None, height=50)
        
        layout.add_widget(self.surname_input)
        layout.add_widget(self.dob_input)
        layout.add_widget(self.gender_input)
        layout.add_widget(self.error_label)
        
        btn_layout = GridLayout(cols=2, size_hint_y=None, height=55, spacing=15)
        back_btn = Button(text='⬅ Back', background_color=(0.4, 0.4, 0.4, 1), bold=True)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'reg_step1'))
        next_btn = Button(text='Next Step ➡', background_color=(0.12, 0.53, 0.90, 1), bold=True)
        next_btn.bind(on_press=self.go_to_next)
        
        btn_layout.add_widget(back_btn)
        btn_layout.add_widget(next_btn)
        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def go_to_next(self, instance):
        global temp_user_data
        surname = self.surname_input.text.strip()
        dob = self.dob_input.text.strip()
        gender = self.gender_input.text.strip().capitalize()
        
        if not surname or not dob or not gender:
            self.error_label.text = "❌ All fields must be filled out."
            return
            
        formatted_dob = dob.replace('/', '-')
        try:
            datetime.datetime.strptime(formatted_dob, '%Y-%m-%d')
        except ValueError:
            self.error_label.text = "❌ Invalid Date format! Use YYYY-MM-DD."
            return
            
        if gender not in ['Male', 'Female']:
            self.error_label.text = "❌ Gender must be strictly 'Male' or 'Female'."
            return
            
        self.error_label.text = ""
        temp_user_data['surname'] = surname
        temp_user_data['dob'] = formatted_dob
        temp_user_data['gender'] = gender
        self.manager.current = 'reg_step3'


# --- STEP 3: Identity & Password ---
class RegStep3(Screen):
    def __init__(self, **kwargs):
        super(RegStep3, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=15)
        set_background(layout, (0.11, 0.13, 0.19, 1))
        
        layout.add_widget(Label(text='[b]Step 3 of 4: Identity & Password[/b]', markup=True, font_size=20, size_hint_y=None, height=40, color=(0.9, 0.9, 0.9, 1)))
        
        self.error_label = Label(text='', font_size=14, size_hint_y=None, height=25, color=(0.9, 0.4, 0.4, 1), halign='center')
        self.error_label.bind(size=self.error_label.setter('text_size'))
        
        self.username_input = TextInput(hint_text='Username (e.g., @student)', multiline=False, size_hint_y=None, height=48)
        self.password_input = TextInput(hint_text='Password (for future sign-ins)', password=True, multiline=False, size_hint_y=None, height=48)
        self.phone_input = TextInput(hint_text='Phone Number or Email', multiline=False, size_hint_y=None, height=48)
        
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(self.phone_input)
        layout.add_widget(self.error_label)
        
        btn_layout = GridLayout(cols=2, size_hint_y=None, height=55, spacing=15)
        back_btn = Button(text='⬅ Back', background_color=(0.4, 0.4, 0.4, 1), bold=True)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'reg_step2'))
        next_btn = Button(text='Next Step ➡', background_color=(0.12, 0.53, 0.90, 1), bold=True)
        next_btn.bind(on_press=self.go_to_next)
        
        btn_layout.add_widget(back_btn)
        btn_layout.add_widget(next_btn)
        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def go_to_next(self, instance):
        global temp_user_data
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        phone = self.phone_input.text.strip()
        
        if not username or not password or not phone:
            self.error_label.text = "❌ All fields are required."
            return
            
        self.error_label.text = ""
        temp_user_data['username'] = username
        temp_user_data['password'] = password
        temp_user_data['phone'] = phone
        self.manager.current = 'reg_step4'


# --- STEP 4: Campus Details & Terms ---
class RegStep4(Screen):
    def __init__(self, **kwargs):
        super(RegStep4, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=30, spacing=15)
        set_background(layout, (0.11, 0.13, 0.19, 1))
        
        layout.add_widget(Label(text='[b]Step 4 of 4: Campus & Terms[/b]', markup=True, font_size=20, size_hint_y=None, height=35, color=(0.9, 0.9, 0.9, 1)))
        
        self.error_label = Label(text='', font_size=14, size_hint_y=None, height=25, color=(0.9, 0.4, 0.4, 1), halign='center')
        self.error_label.bind(size=self.error_label.setter('text_size'))
        
        self.univ_input = TextInput(hint_text='University / Polytechnic Name', multiline=False, size_hint_y=None, height=45)
        self.location_input = TextInput(hint_text='Campus Residence / Location', multiline=False, size_hint_y=None, height=45)
        
        layout.add_widget(self.univ_input)
        layout.add_widget(self.location_input)
        
        terms_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        self.agree_checkbox = CheckBox(size_hint=(None, None), size=(40, 40))
        
        terms_label_btn = Button(text='I agree to the Terms & Conditions', background_color=(0, 0, 0, 0), color=(0.9, 0.9, 0.9, 1), halign='left', valign='middle', font_size=14)
        terms_label_btn.bind(size=terms_label_btn.setter('text_size'))
        terms_label_btn.bind(on_press=self.show_terms_popup)
        
        view_terms_btn = Button(text='View Terms', size_hint=(None, None), size=(90, 38), background_color=(0.12, 0.53, 0.90, 1), font_size=12, bold=True)
        view_terms_btn.bind(on_press=self.show_terms_popup)
        
        terms_layout.add_widget(self.agree_checkbox)
        terms_layout.add_widget(terms_label_btn)
        terms_layout.add_widget(view_terms_btn)
        
        layout.add_widget(terms_layout)
        layout.add_widget(self.error_label)
        
        btn_layout = GridLayout(cols=2, size_hint_y=None, height=50, spacing=15)
        back_btn = Button(text='⬅ Back', background_color=(0.4, 0.4, 0.4, 1), bold=True)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'reg_step3'))
        submit_btn = Button(text='Send Code ✉', background_color=(0.18, 0.70, 0.44, 1), bold=True)
        submit_btn.bind(on_press=self.send_code)
        
        btn_layout.add_widget(back_btn)
        btn_layout.add_widget(submit_btn)
        layout.add_widget(btn_layout)
        self.add_widget(layout)

    def show_terms_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        content.add_widget(Label(text='[b]Campus Hub Terms & Conditions[/b]', markup=True, font_size=16, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=30))
        
        terms_text = (
            "1. Acceptance of Terms: By registering and using Campus Hub, you agree to comply with all community guidelines.\n\n"
            "2. User Conduct: Harassment, hate speech, sharing malicious links, or fraudulent posts are strictly prohibited.\n\n"
            "3. Marketplace: Transactions for notes and student resources are peer-to-peer via EcoCash.\n\n"
            "4. Privacy: Your data is stored locally on your device/database securely."
        )
        scroll = ScrollView(size_hint=(1, 1))
        terms_lbl = Label(text=terms_text, color=(0.8, 0.8, 0.8, 1), halign='left', valign='top')
        terms_lbl.bind(size=terms_lbl.setter('text_size'))
        scroll.add_widget(terms_lbl)
        content.add_widget(scroll)
        
        close_btn = Button(text='Close', size_hint_y=None, height=45, background_color=(0.4, 0.4, 0.4, 1), bold=True)
        popup = Popup(title='Terms and Conditions', content=content, size_hint=(0.85, 0.75))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def send_code(self, instance):
        global temp_user_data, generated_code, code_expiry_time
        univ = self.univ_input.text.strip()
        location = self.location_input.text.strip()
        
        if not univ or not location:
            self.error_label.text = "❌ University and Location cannot be blank."
            return
            
        if not self.agree_checkbox.active:
            self.error_label.text = "❌ You must accept the Terms & Conditions."
            return
            
        self.error_label.text = ""
        temp_user_data['university'] = univ
        temp_user_data['location'] = location
        temp_user_data['bio'] = f"Student at {univ}"
        
        generated_code = str(random.randint(1000, 9999))
        code_expiry_time = time.time() + 60
        print(f"\n[SECURE EMAIL] To: {temp_user_data['phone']} | Code: {generated_code}\n")
        self.manager.current = 'verify'


# --- VERIFICATION SCREEN ---
class VerifyScreen(Screen):
    def __init__(self, **kwargs):
        super(VerifyScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=40, spacing=20)
        set_background(layout, (0.11, 0.13, 0.19, 1))
        
        layout.add_widget(Label(text='[b]Security Verification[/b]', markup=True, font_size=22, size_hint_y=None, height=40, color=(0.9, 0.9, 0.9, 1)))
        self.timer_label = Label(text='Code expires in: 60s', halign='center', size_hint_y=None, height=40, color=(0.9, 0.6, 0.2, 1))
        layout.add_widget(self.timer_label)
        
        self.code_input = TextInput(hint_text='----', multiline=False, font_size=32, size_hint_y=None, height=60, halign='center')
        layout.add_widget(self.code_input)
        
        self.verify_btn = Button(text='Confirm & Register Account 🚀', size_hint_y=None, height=55, background_color=(0.18, 0.70, 0.44, 1), bold=True)
        self.verify_btn.bind(on_press=self.verify_code)
        layout.add_widget(self.verify_btn)
        
        self.resend_btn = Button(text='Resend Code 🔄', size_hint_y=None, height=45, background_color=(0.12, 0.53, 0.90, 1), bold=True, disabled=True)
        self.resend_btn.bind(on_press=self.resend_code)
        layout.add_widget(self.resend_btn)
        self.add_widget(layout)

    def on_enter(self):
        self.time_left = 60
        self.resend_btn.disabled = True
        self.verify_btn.disabled = False
        self.code_input.text = ''
        if hasattr(self, 'clock_event') and self.clock_event:
            self.clock_event.cancel()
        self.clock_event = Clock.schedule_interval(self.update_timer, 1)

    def update_timer(self, dt):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.text = f'Code expires in: {self.time_left}s'
        else:
            self.timer_label.text = '❌ Code Expired!'
            self.verify_btn.disabled = True
            self.resend_btn.disabled = False
            return False

    def resend_code(self, instance):
        global generated_code, code_expiry_time
        generated_code = str(random.randint(1000, 9999))
        code_expiry_time = time.time() + 60
        print(f"\n[SECURE EMAIL] NEW Code: {generated_code}\n")
        self.on_enter()

    def verify_code(self, instance):
        global temp_user_data, generated_code, code_expiry_time, active_username
        if time.time() > code_expiry_time:
            self.timer_label.text = '❌ Code has expired!'
            return
            
        if self.code_input.text.strip() == generated_code:
            if hasattr(self, 'clock_event') and self.clock_event:
                self.clock_event.cancel()
                
            active_username = temp_user_data.get('username')
            conn = sqlite3.connect('campus_app.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (name, surname, dob, gender, username, password, phone, university, location, bio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                temp_user_data.get('name'), temp_user_data.get('surname'), temp_user_data.get('dob'),
                temp_user_data.get('gender'), active_username, temp_user_data.get('password'),
                temp_user_data.get('phone'), temp_user_data.get('university'), temp_user_data.get('location'),
                temp_user_data.get('bio')
            ))
            conn.commit()
            conn.close()
            self.manager.current = 'main_dashboard'
        else:
            self.code_input.text = ''
            self.code_input.hint_text = '❌ Invalid Code!'


# --- MAIN DASHBOARD SCREEN ---
class MainDashboardScreen(Screen):
    def __init__(self, **kwargs):
        super(MainDashboardScreen, self).__init__(**kwargs)
        root_layout = BoxLayout(orientation='vertical', padding=12, spacing=10)
        set_background(root_layout, (0.08, 0.09, 0.13, 1))
        
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        title_label = Label(text='[b]🎓 Campus Hub v1.0[/b]', markup=True, font_size=20, halign='left', valign='middle', color=(0.9, 0.9, 0.9, 1))
        title_label.bind(size=title_label.setter('text_size'))
        header_layout.add_widget(title_label)
        
        menu_btn = Button(text='+', font_size=22, size_hint=(None, None), size=(45, 45), background_color=(0.12, 0.53, 0.90, 1), bold=True)
        menu_btn.bind(on_press=self.open_action_menu)
        header_layout.add_widget(menu_btn)
        
        logout_btn = Button(text='Logout', font_size=12, size_hint=(None, None), size=(60, 45), background_color=(0.85, 0.2, 0.2, 1), bold=True)
        logout_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'welcome'))
        header_layout.add_widget(logout_btn)
        root_layout.add_widget(header_layout)
        
        self.search_input = TextInput(hint_text='🔍 Search username, contact, or area...', size_hint_y=None, height=42, multiline=False)
        self.search_input.bind(text=self.on_search_text)
        root_layout.add_widget(self.search_input)
        
        self.post_input = TextInput(hint_text="What's happening? Share text or YouTube links...", size_hint_y=None, height=65, multiline=True)
        root_layout.add_widget(self.post_input)
        
        media_btn_layout = GridLayout(cols=4, size_hint_y=None, height=42, spacing=6)
        post_btn = Button(text='Post Feed', background_color=(0.18, 0.70, 0.44, 1), bold=True)
        post_btn.bind(on_press=lambda x: self.add_public_post('text'))
        
        notes_btn = Button(text='Sell PDF', background_color=(0.85, 0.55, 0.12, 1), bold=True)
        notes_btn.bind(on_press=self.open_sell_pdf_popup)
        
        gallery_btn = Button(text='Gallery', background_color=(0.12, 0.53, 0.90, 1), bold=True)
        gallery_btn.bind(on_press=lambda x: self.add_public_post('image_gallery'))
        
        camera_btn = Button(text='Camera', background_color=(0.7, 0.2, 0.7, 1), bold=True)
        camera_btn.bind(on_press=lambda x: self.add_public_post('image_camera'))
        
        media_btn_layout.add_widget(post_btn)
        media_btn_layout.add_widget(notes_btn)
        media_btn_layout.add_widget(gallery_btn)
        media_btn_layout.add_widget(camera_btn)
        root_layout.add_widget(media_btn_layout)
        
        self.feed_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        self.feed_layout.bind(minimum_height=self.feed_layout.setter('height'))
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.scroll_view.add_widget(self.feed_layout)
        root_layout.add_widget(self.scroll_view)
        
        self.add_widget(root_layout)

    def on_enter(self):
        self.load_posts()

    def open_sell_pdf_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=15, spacing=12)
        content.add_widget(Label(text='[b]Upload Study PDF Document for Sale[/b]', markup=True, font_size=16, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=30))
        
        self.sell_desc_input = TextInput(hint_text='Document Title / Description', multiline=True, size_hint_y=None, height=60)
        self.sell_price_input = TextInput(hint_text='Price (e.g. $2.00)', multiline=False, size_hint_y=None, height=42)
        self.sell_ecocash_input = TextInput(hint_text='Your EcoCash Merchant Code or Number', multiline=False, size_hint_y=None, height=42)
        
        file_picker_btn = Button(text='📁 Browse PDF File', size_hint_y=None, height=45, background_color=(0.12, 0.53, 0.90, 1), bold=True)
        file_picker_btn.bind(on_press=self.open_file_chooser)
        
        self.selected_file_lbl = Label(text='No PDF file selected yet.', color=(0.9, 0.7, 0.2, 1), size_hint_y=None, height=25)
        self.chosen_pdf_path = ""
        self.sell_error_lbl = Label(text='', color=(0.9, 0.4, 0.4, 1), size_hint_y=None, height=25)
        
        content.add_widget(self.sell_desc_input)
        content.add_widget(self.sell_price_input)
        content.add_widget(self.sell_ecocash_input)
        content.add_widget(file_picker_btn)
        content.add_widget(self.selected_file_lbl)
        content.add_widget(self.sell_error_lbl)
        
        publish_btn = Button(text='Post Publicly for Sale 🚀', background_color=(0.18, 0.70, 0.44, 1), size_hint_y=None, height=50, bold=True)
        publish_btn.bind(on_press=self.submit_marketplace_post)
        content.add_widget(publish_btn)
        
        self.sell_popup = Popup(title='Marketplace Studio', content=content, size_hint=(0.85, 0.82))
        self.sell_popup.open()

    def open_file_chooser(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text='Select PDF Document', size_hint_y=None, height=30))
        filechooser = FileChooserListView(filters=['*.pdf', '*.txt', '*.docx'])
        content.add_widget(filechooser)
        
        select_btn = Button(text='Select File', size_hint_y=None, height=45, background_color=(0.18, 0.70, 0.44, 1), bold=True)
        
        def on_file_selected(btn):
            if filechooser.selection:
                self.chosen_pdf_path = filechooser.selection[0]
                filename = os.path.basename(self.chosen_pdf_path)
                self.selected_file_lbl.text = f"Selected: {filename}"
                chooser_popup.dismiss()

        select_btn.bind(on_press=on_file_selected)
        content.add_widget(select_btn)
        chooser_popup = Popup(title='File Browser', content=content, size_hint=(0.85, 0.85))
        chooser_popup.open()

    def submit_marketplace_post(self, instance):
        global active_username
        desc = self.sell_desc_input.text.strip()
        price = self.sell_price_input.text.strip()
        ecocash = self.sell_ecocash_input.text.strip()
        
        if not desc or not price or not ecocash or not self.chosen_pdf_path:
            self.sell_error_lbl.text = "❌ All fields and a PDF file must be provided!"
            return
            
        filename = os.path.basename(self.chosen_pdf_path)
        dest_path = os.path.join('downloads', filename)
        try:
            shutil.copy(self.chosen_pdf_path, dest_path)
        except Exception:
            dest_path = self.chosen_pdf_path
            
        conn = sqlite3.connect('campus_app.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO posts (post_text, post_type, media_path, price, seller_username, seller_ecocash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (desc, 'marketplace_pdf', dest_path, price, active_username or '@student', ecocash))
        conn.commit()
        conn.close()
        
        self.sell_popup.dismiss()
        self.load_posts()

    def load_posts(self):
        self.feed_layout.clear_widgets()
        conn = sqlite3.connect('campus_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, post_text, post_type, media_path, price, seller_username, seller_ecocash FROM posts ORDER BY id DESC')
        rows = cursor.fetchall()
        
        for row in rows:
            post_id, text, p_type, m_path, price, seller, ecocash = row[0], row[1], row[2], row[3], row[4], row[5], row[6]
            
            if p_type == 'marketplace_pdf':
                cursor.execute('SELECT id FROM purchases WHERE post_id = ? AND buyer_username = ?', (post_id, active_username))
                purchased = cursor.fetchone()
                is_seller = (active_username == seller)
                
                post_card = BoxLayout(orientation='vertical', padding=12, size_hint_y=None, height=140)
                set_background(post_card, (0.22, 0.18, 0.10, 1))
                
                info_text = f"📚 [MARKETPLACE PDF]\n{text}\n💰 Price: {price} | 👤 Seller: {seller}\n📱 EcoCash Code/Number: {ecocash}"
                lbl = Label(text=info_text, size_hint_y=None, height=75, halign='left', valign='middle', color=(0.9, 0.9, 0.9, 1))
                lbl.bind(size=lbl.setter('text_size'))
                post_card.add_widget(lbl)
                
                if is_seller or purchased:
                    open_btn = Button(text='📖 Open & Download Document', size_hint_y=None, height=40, background_color=(0.18, 0.70, 0.44, 1), bold=True)
                    open_btn.bind(on_press=lambda x, path=m_path, desc=text: self.show_document_viewer(desc, path))
                    post_card.add_widget(open_btn)
                else:
                    buy_btn = Button(text=f'💳 Pay via EcoCash ({price})', size_hint_y=None, height=40, background_color=(0.85, 0.55, 0.12, 1), bold=True)
                    buy_btn.bind(on_press=lambda x, pid=post_id, pr=price, ec=ecocash, path=m_path, desc=text: self.open_ecocash_payment_popup(pid, pr, ec, path, desc))
                    post_card.add_widget(buy_btn)
            else:
                author = seller if seller else "@student"
                card_text = f"👤 Posted by: [b]{author}[/b]\n💬 {text}"
                card_color = (0.15, 0.17, 0.24, 1)
                
                if p_type == 'image_gallery':
                    card_text += f"\n[🖼 Attached Photo: {m_path}]"
                elif p_type == 'image_camera':
                    card_text += f"\n[📷 Camera Snapshot: {m_path}]"
                elif p_type == 'live_stream':
                    card_text = f"👤 Broadcast by: [b]{author}[/b]\n🔴 [LIVE STREAM BROADCAST]\n{text}"
                    card_color = (0.3, 0.1, 0.1, 1)
                    
                post_card = BoxLayout(orientation='vertical', padding=10, size_hint_y=None, height=110 if p_type == 'live_stream' else 90)
                set_background(post_card, card_color)
                
                post_label = Label(text=card_text, markup=True, size_hint_y=None, height=90, halign='left', valign='middle', color=(0.9, 0.9, 0.9, 1))
                post_label.bind(size=post_label.setter('text_size'))
                post_card.add_widget(post_label)
                
            self.feed_layout.add_widget(post_card)
        conn.close()

    def open_ecocash_payment_popup(self, post_id, price, seller_ecocash, media_path, description):
        content = BoxLayout(orientation='vertical', padding=15, spacing=12)
        content.add_widget(Label(text='[b]EcoCash Payment Gateway[/b]', markup=True, font_size=18, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=35))
        content.add_widget(Label(text=f"Pay to Seller Account: [b]{seller_ecocash}[/b]\nAmount: [b]{price}[/b]", markup=True, color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=45))
        
        info_lbl = Label(text="Tap the button below to launch EcoCash USSD dialer string on your phone network.", color=(0.7, 0.8, 0.7, 1), halign='center', size_hint_y=None, height=40)
        info_lbl.bind(size=info_lbl.setter('text_size'))
        content.add_widget(info_lbl)
        
        dial_btn = Button(text='📳 Dial EcoCash USSD Code (*151#)', background_color=(0.18, 0.70, 0.44, 1), size_hint_y=None, height=50, bold=True)
        
        def launch_dialer(instance):
            clean_price = price.replace('$', '').strip()
            ussd_string = f"tel:*151*2*1*{seller_ecocash}*{clean_price}%23"
            try:
                webbrowser.open(ussd_string)
            except Exception:
                pass
                
            conn = sqlite3.connect('campus_app.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO purchases (post_id, buyer_username) VALUES (?, ?)', (post_id, active_username))
            conn.commit()
            conn.close()
            
            self.pay_popup.dismiss()
            self.load_posts()
            self.show_document_viewer(description, media_path)

        dial_btn.bind(on_press=launch_dialer)
        content.add_widget(dial_btn)
        
        close_btn = Button(text='Cancel', size_hint_y=None, height=40, background_color=(0.4, 0.4, 0.4, 1), bold=True)
        self.pay_popup = Popup(title='Secure EcoCash Checkout', content=content, size_hint=(0.85, 0.65))
        close_btn.bind(on_press=self.pay_popup.dismiss)
        content.add_widget(close_btn)
        self.pay_popup.open()

    def show_document_viewer(self, description, media_path):
        content = BoxLayout(orientation='vertical', padding=15, spacing=12)
        content.add_widget(Label(text=f'[b]📄 Document Viewer[/b]\n{description}', markup=True, font_size=15, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=55))
        
        doc_box = BoxLayout(orientation='vertical', padding=15, spacing=8)
        set_background(doc_box, (0.13, 0.15, 0.22, 1))
        
        filename = os.path.basename(media_path)
        doc_content_lbl = Label(text=f"🔓 UNLOCKED DOCUMENT\n\nFile Location: {media_path}\n\nUnlocked successfully for {active_username}.", halign='center', valign='middle', color=(0.9, 0.9, 0.9, 1))
        doc_content_lbl.bind(size=doc_content_lbl.setter('text_size'))
        doc_box.add_widget(doc_content_lbl)
        
        download_btn = Button(text='⬇ Save PDF to Downloads Folder', size_hint_y=None, height=45, background_color=(0.12, 0.53, 0.90, 1), bold=True)
        
        def download_file(btn):
            try:
                dest = os.path.join(os.getcwd(), 'downloads', filename)
                if os.path.exists(media_path):
                    shutil.copy(media_path, dest)
                    doc_content_lbl.text = f"✅ SUCCESS!\nPDF saved to: {dest}"
                else:
                    doc_content_lbl.text = "❌ Source file path missing."
            except Exception as e:
                doc_content_lbl.text = f"❌ Error: {str(e)}"

        download_btn.bind(on_press=download_file)
        doc_box.add_widget(download_btn)
        content.add_widget(doc_box)
        
        close_btn = Button(text='Close Viewer', size_hint_y=None, height=45, background_color=(0.4, 0.4, 0.4, 1), bold=True)
        popup = Popup(title='Secure Study Document', content=content, size_hint=(0.85, 0.8))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

    def on_search_text(self, instance, query):
        query = query.strip().lower()
        if not query:
            self.load_posts()
            return
            
        self.feed_layout.clear_widgets()
        conn = sqlite3.connect('campus_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT name, surname, username, phone, location, university FROM users WHERE username LIKE ? OR phone LIKE ? OR name LIKE ?', 
                       (f'%{query}%', f'%{query}%', f'%{query}%'))
        users = cursor.fetchall()
        
        if users:
            header = Label(text=f'[b]Found Users Matching "{query}":[/b]', markup=True, size_hint_y=None, height=30, color=(0.2, 0.8, 0.4, 1))
            self.feed_layout.add_widget(header)
            for u in users:
                card = BoxLayout(orientation='vertical', padding=8, size_hint_y=None, height=60)
                set_background(card, (0.15, 0.22, 0.20, 1))
                lbl = Label(text=f"👤 {u[0]} {u[1]} ({u[2]}) | 📍 {u[4]}", size_hint_y=None, height=40, color=(0.9, 0.9, 0.9, 1))
                card.add_widget(lbl)
                self.feed_layout.add_widget(card)
        else:
            not_found_lbl = Label(text=f'[b]❌ User not found. Local peers:[/b]', markup=True, size_hint_y=None, height=30, color=(0.9, 0.4, 0.4, 1))
            self.feed_layout.add_widget(not_found_lbl)
            
            cursor.execute('SELECT name, surname, username, location FROM users LIMIT 5')
            local_users = cursor.fetchall()
            for lu in local_users:
                card = BoxLayout(orientation='vertical', padding=8, size_hint_y=None, height=60)
                set_background(card, (0.22, 0.17, 0.15, 1))
                lbl = Label(text=f"📍 Local Student: {lu[0]} {lu[1]} - Residence: {lu[3]}", size_hint_y=None, height=40, color=(0.9, 0.9, 0.9, 1))
                card.add_widget(lbl)
                self.feed_layout.add_widget(card)
        conn.close()

    def add_public_post(self, post_type):
        global active_username
        text = self.post_input.text.strip()
        media_path = ""
        if post_type == 'image_gallery':
            media_path = "gallery_photo.jpg"
            if not text: text = "Shared an image."
        elif post_type == 'image_camera':
            media_path = "camera_snap.jpg"
            if not text: text = "Camera snapshot."
            
        if text or media_path:
            conn = sqlite3.connect('campus_app.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO posts (post_text, post_type, media_path, price, seller_username, seller_ecocash) VALUES (?, ?, ?, ?, ?, ?)', 
                           (text, post_type, media_path, '0', active_username or '@student', ''))
            conn.commit()
            conn.close()
            self.load_posts()
            self.post_input.text = ''

    def open_action_menu(self, instance):
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        content.add_widget(Label(text='[b]Advanced Actions & Media Studio[/b]', markup=True, font_size=18, color=(0.9, 0.9, 0.9, 1)))
        
        bio_btn = Button(text='Update Bio', background_color=(0.12, 0.53, 0.90, 1), bold=True)
        bio_btn.bind(on_press=self.open_bio_popup)
        
        tx_history_btn = Button(text='📊 View Transaction History', background_color=(0.18, 0.70, 0.44, 1), bold=True)
        tx_history_btn.bind(on_press=self.open_transaction_history_popup)
        
        vid_call_btn = Button(text='Start Video Call', background_color=(0.12, 0.53, 0.90, 1), bold=True)
        vid_call_btn.bind(on_press=self.open_video_call_popup)
        
        live_btn = Button(text='Go Live (Live Stream)', background_color=(0.85, 0.2, 0.2, 1), bold=True)
        live_btn.bind(on_press=self.open_live_stream_popup)
        
        support_btn = Button(text='Support Developer', background_color=(0.85, 0.55, 0.12, 1), bold=True)
        support_btn.bind(on_press=self.open_ecocash_popup)
        
        feedback_btn = Button(text='Send Feedback & Bug Report', background_color=(0.7, 0.2, 0.7, 1), bold=True)
        feedback_btn.bind(on_press=self.open_feedback_popup)
        
        content.add_widget(bio_btn)
        content.add_widget(tx_history_btn)
        content.add_widget(vid_call_btn)
        content.add_widget(live_btn)
        content.add_widget(support_btn)
        content.add_widget(feedback_btn)
        
        self.popup = Popup(title='Media & Developer Studio', content=content, size_hint=(0.85, 0.75))
        self.popup.open()

    def open_transaction_history_popup(self, instance):
        if hasattr(self, 'popup') and self.popup: self.popup.dismiss()
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        content.add_widget(Label(text='[b]Completed Purchase History[/b]', markup=True, font_size=16, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=30))
        
        tx_scroll = ScrollView(size_hint=(1, 1))
        tx_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        tx_layout.bind(minimum_height=tx_layout.setter('height'))
        
        conn = sqlite3.connect('campus_app.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, posts.post_text, posts.price, p.buyer_username, p.timestamp 
            FROM purchases p 
            JOIN posts ON p.post_id = posts.id 
            ORDER BY p.id DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            for row in rows:
                card = BoxLayout(orientation='vertical', padding=8, size_hint_y=None, height=75)
                set_background(card, (0.15, 0.22, 0.20, 1))
                txt = f"📦 Item: {row[1][:35]}...\n💰 Price: {row[2]} | Buyer: {row[3]}\n🕒 Time: {row[4]}"
                lbl = Label(text=txt, size_hint_y=None, height=60, color=(0.9, 0.9, 0.9, 1), font_size=12)
                lbl.bind(size=lbl.setter('text_size'))
                card.add_widget(lbl)
                tx_layout.add_widget(card)
        else:
            tx_layout.add_widget(Label(text="No transactions recorded yet.", color=(0.7, 0.7, 0.7, 1), size_hint_y=None, height=40))
            
        tx_scroll.add_widget(tx_layout)
        content.add_widget(tx_scroll)
        
        close_btn = Button(text='Close', size_hint_y=None, height=45, background_color=(0.4, 0.4, 0.4, 1), bold=True)
        tx_popup = Popup(title='Transaction Log', content=content, size_hint=(0.85, 0.75))
        close_btn.bind(on_press=tx_popup.dismiss)
        content.add_widget(close_btn)
        tx_popup.open()

    def open_bio_popup(self, instance):
        if hasattr(self, 'popup') and self.popup: self.popup.dismiss()
        content = BoxLayout(orientation='vertical', padding=15, spacing=12)
        content.add_widget(Label(text='[b]Update Your Student Bio[/b]', markup=True, font_size=16, color=(0.9, 0.9, 0.9, 1)))
        
        self.bio_edit_input = TextInput(hint_text='Write your new student bio...', multiline=True, size_hint_y=None, height=100)
        content.add_widget(self.bio_edit_input)
        
        save_bio_btn = Button(text='Save Bio 💾', background_color=(0.18, 0.70, 0.44, 1), bold=True)
        def save_bio(btn):
            global active_username
            new_bio = self.bio_edit_input.text.strip()
            if new_bio:
                conn = sqlite3.connect('campus_app.db')
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET bio = ? WHERE username = ?', (new_bio, active_username))
                conn.commit()
                conn.close()
                self.bio_popup.dismiss()
        save_bio_btn.bind(on_press=save_bio)
        content.add_widget(save_bio_btn)
        self.bio_popup = Popup(title='Profile Settings', content=content, size_hint=(0.8, 0.5))
        self.bio_popup.open()

    def open_video_call_popup(self, instance):
        if hasattr(self, 'popup') and self.popup: self.popup.dismiss()
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text='[b]Secure Peer-to-Peer Video Call[/b]', markup=True, size_hint_y=None, height=30, color=(0.9, 0.9, 0.9, 1)))
        try:
            cam = Camera(play=True, resolution=(-1, -1), size_hint=(1, 1))
            content.add_widget(cam)
        except Exception:
            content.add_widget(Label(text='📷 Webcam provider unavailable on this environment.', halign='center', color=(0.9, 0.6, 0.2, 1)))
        end_btn = Button(text='End Video Call', size_hint_y=None, height=45, background_color=(0.8, 0.2, 0.2, 1), bold=True)
        popup = Popup(title='Video Call Active', content=content, size_hint=(0.85, 0.8))
        end_btn.bind(on_press=popup.dismiss)
        content.add_widget(end_btn)
        popup.open()

    def open_live_stream_popup(self, instance):
        if hasattr(self, 'popup') and self.popup: self.popup.dismiss()
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text='[b]Live Stream Broadcast Studio[/b]', markup=True, size_hint_y=None, height=30, color=(0.9, 0.2, 0.2, 1)))
        try:
            cam = Camera(play=True, resolution=(-1, -1), size_hint=(1, 1))
            content.add_widget(cam)
        except Exception:
            content.add_widget(Label(text='🔴 Camera hardware not detected. Broadcast text update instead!', halign='center', color=(0.9, 0.6, 0.2, 1)))
        
        broadcast_btn = Button(text='Broadcast Live to Feed 🔴', size_hint_y=None, height=45, background_color=(0.18, 0.70, 0.44, 1), bold=True)
        def start_broadcast(btn):
            global active_username
            conn = sqlite3.connect('campus_app.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO posts (post_text, post_type, media_path, price, seller_username, seller_ecocash) VALUES (?, ?, ?, ?, ?, ?)', 
                           ("Started a live broadcast on Campus Hub!", "live_stream", "webcam_stream", '0', active_username or '@student', ''))
            conn.commit()
            conn.close()
            self.load_posts()
            popup.dismiss()
        broadcast_btn.bind(on_press=start_broadcast)
        content.add_widget(broadcast_btn)
        popup = Popup(title='Live Stream Hub', content=content, size_hint=(0.85, 0.8))
        popup.open()

    def open_ecocash_popup(self, instance):
        if hasattr(self, 'popup') and self.popup: self.popup.dismiss()
        conn = sqlite3.connect('campus_app.db')
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM app_settings WHERE key = ?', ('ecocash_number',))
        row = cursor.fetchone()
        secure_number = row[0] if row else "0777907187"
        conn.close()
            
        content = BoxLayout(orientation='vertical', padding=15, spacing=12)
        content.add_widget(Label(text='[b]Support Developer[/b]', markup=True, font_size=16, color=(0.9, 0.9, 0.9, 1), size_hint_y=None, height=30))
        content.add_widget(Label(text=f"Merchant Channel: [b]{ECOCASH_NAME}[/b]", markup=True, color=(0.8, 0.8, 0.8, 1), size_hint_y=None, height=30))
        
        self.dev_pay_amount = TextInput(hint_text='Support Amount (e.g. 1.00)', multiline=False, size_hint_y=None, height=45)
        content.add_widget(self.dev_pay_amount)
        
        dial_dev_btn = Button(text='📳 Dial Merchant USSD Code', background_color=(0.18, 0.70, 0.44, 1), size_hint_y=None, height=50, bold=True)
        
        def process_dev_support(btn):
            amount = self.dev_pay_amount.text.strip()
            if not amount:
                return
            clean_amount = amount.replace('$', '').strip()
            ussd_string = f"tel:*151*2*1*{secure_number}*{clean_amount}%23"
            try:
                webbrowser.open(ussd_string)
            except Exception:
                pass
            print(f"\n[ECOCASH SUPPORT] USSD String launched for Merchant: {secure_number} | Amount: {clean_amount}\n")
            self.dev_support_popup.dismiss()
            
        dial_dev_btn.bind(on_press=process_dev_support)
        content.add_widget(dial_dev_btn)
        
        close_btn = Button(text='Cancel', size_hint_y=None, height=40, background_color=(0.4, 0.4, 0.4, 1), bold=True)
        self.dev_support_popup = Popup(title='Secure EcoCash Support', content=content, size_hint=(0.85, 0.65))
        close_btn.bind(on_press=self.dev_support_popup.dismiss)
        self.dev_support_popup.open()

    def open_feedback_popup(self, instance):
        if hasattr(self, 'popup') and self.popup: self.popup.dismiss()
        content = BoxLayout(orientation='vertical', padding=15, spacing=12)
        content.add_widget(Label(text='[b]Send Feedback to Developer[/b]\n(Delivered securely to support team)', markup=True, font_size=14, color=(0.9, 0.9, 0.9, 1), halign='center'))
        
        self.feedback_input = TextInput(hint_text='Write your feedback or bug report here...', multiline=True, size_hint_y=None, height=100)
        content.add_widget(self.feedback_input)
        
        submit_fb_btn = Button(text='Send Feedback 🚀', background_color=(0.18, 0.70, 0.44, 1), bold=True)
        def save_and_email_feedback(btn):
            global active_username
            fb_text = self.feedback_input.text.strip()
            if fb_text:
                conn = sqlite3.connect('campus_app.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO feedback (username, feedback_text) VALUES (?, ?)', (active_username or '@student', fb_text))
                conn.commit()
                conn.close()
                print(f"\n[FEEDBACK LOG] From: {active_username or '@student'} | Text: {fb_text}\n")
                self.fb_popup.dismiss()
        submit_fb_btn.bind(on_press=save_and_email_feedback)
        content.add_widget(submit_fb_btn)
        
        self.fb_popup = Popup(title='Feedback Hub', content=content, size_hint=(0.8, 0.5))
        self.fb_popup.open()


# --- APP CONTROLLER ---
class CampusApp(App):
    icon = 'campus_icon.ico'

    def build(self):
        init_db()
        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(SignInScreen(name='signin'))
        sm.add_widget(RegStep1(name='reg_step1'))
        sm.add_widget(RegStep2(name='reg_step2'))
        sm.add_widget(RegStep3(name='reg_step3'))
        sm.add_widget(RegStep4(name='reg_step4'))
        sm.add_widget(VerifyScreen(name='verify'))
        sm.add_widget(MainDashboardScreen(name='main_dashboard'))
        return sm

if __name__ == '__main__':
    CampusApp().run()