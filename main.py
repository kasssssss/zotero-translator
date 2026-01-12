"""
Zotero Translation Assistant
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle

import threading

from translator import TranslatorService


# Android utilities
def vibrate(duration=100):
    """Vibrate device (Android only)"""
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            activity = PythonActivity.mActivity
            vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
            vibrator.vibrate(duration)
        except:
            pass


def show_toast(message):
    """Show toast message (Android only)"""
    if platform == 'android':
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread
            
            @run_on_ui_thread
            def _show_toast(msg):
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Toast = autoclass('android.widget.Toast')
                context = PythonActivity.mActivity
                toast = Toast.makeText(context, msg, Toast.LENGTH_SHORT)
                toast.show()
            
            _show_toast(message)
        except:
            pass


class AndroidForegroundService:
    """Android Foreground Service for background clipboard monitoring"""
    
    def __init__(self):
        self.notification_id = 1001
        self.channel_id = "ZoteroTranslator"
        self.is_running = False
    
    def start(self):
        """Start foreground service with notification"""
        if platform != 'android':
            return
        
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            NotificationBuilder = autoclass('android.app.Notification$Builder')
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationManager = autoclass('android.app.NotificationManager')
            PendingIntent = autoclass('android.app.PendingIntent')
            Intent = autoclass('android.content.Intent')
            Build = autoclass('android.os.Build')
            
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()
            
            # Create notification channel (Android 8.0+)
            if Build.VERSION.SDK_INT >= 26:
                channel = NotificationChannel(
                    self.channel_id,
                    "Zotero Translator",
                    NotificationManager.IMPORTANCE_LOW
                )
                channel.setDescription("Clipboard monitoring service")
                nm = context.getSystemService(Context.NOTIFICATION_SERVICE)
                nm.createNotificationChannel(channel)
            
            # Create notification
            intent = activity.getIntent()
            pending_intent = PendingIntent.getActivity(
                context, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            )
            
            if Build.VERSION.SDK_INT >= 26:
                builder = NotificationBuilder(context, self.channel_id)
            else:
                builder = NotificationBuilder(context)
            
            builder.setContentTitle("Zotero Translator")
            builder.setContentText("Monitoring clipboard...")
            builder.setSmallIcon(activity.getApplicationInfo().icon)
            builder.setContentIntent(pending_intent)
            builder.setOngoing(True)
            
            notification = builder.build()
            
            # Show notification
            nm = context.getSystemService(Context.NOTIFICATION_SERVICE)
            nm.notify(self.notification_id, notification)
            
            self.is_running = True
            print("Foreground service started")
            
        except Exception as e:
            print(f"Foreground service error: {e}")
    
    def stop(self):
        """Stop foreground service"""
        if platform != 'android':
            return
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()
            
            nm = context.getSystemService(Context.NOTIFICATION_SERVICE)
            nm.cancel(self.notification_id)
            
            self.is_running = False
            print("Foreground service stopped")
            
        except Exception as e:
            print(f"Stop service error: {e}")
    
    def update_notification(self, text):
        """Update notification text"""
        if platform != 'android' or not self.is_running:
            return
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            NotificationBuilder = autoclass('android.app.Notification$Builder')
            PendingIntent = autoclass('android.app.PendingIntent')
            Build = autoclass('android.os.Build')
            
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()
            
            intent = activity.getIntent()
            pending_intent = PendingIntent.getActivity(
                context, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            )
            
            if Build.VERSION.SDK_INT >= 26:
                builder = NotificationBuilder(context, self.channel_id)
            else:
                builder = NotificationBuilder(context)
            
            builder.setContentTitle("Zotero Translator")
            builder.setContentText(text)
            builder.setSmallIcon(activity.getApplicationInfo().icon)
            builder.setContentIntent(pending_intent)
            builder.setOngoing(True)
            
            notification = builder.build()
            
            nm = context.getSystemService(Context.NOTIFICATION_SERVICE)
            nm.notify(self.notification_id, notification)
            
        except Exception as e:
            print(f"Update notification error: {e}")


class FloatingBubble:
    """Placeholder for floating bubble"""
    def __init__(self):
        self.is_showing = False
    def show(self, status=""):
        pass
    def hide(self):
        pass


class SettingsPopup(Popup):
    """Settings popup"""
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.title = "Settings"
        self.size_hint = (0.9, 0.85)
        
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))
        
        # API Key
        api_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        api_section.add_widget(Label(text="API Key:", size_hint_y=None, height=dp(25)))
        self.api_key_input = TextInput(
            text=self.app.config_store.get('settings')['api_key'] if self.app.config_store.exists('settings') else '',
            multiline=False,
            password=True,
            size_hint_y=None,
            height=dp(45),
            hint_text="Enter SiliconFlow API Key"
        )
        api_section.add_widget(self.api_key_input)
        layout.add_widget(api_section)
        
        # API URL
        url_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        url_section.add_widget(Label(text="API URL:", size_hint_y=None, height=dp(25)))
        self.api_url_input = TextInput(
            text=self.app.config_store.get('settings')['api_url'] if self.app.config_store.exists('settings') else 'https://api.siliconflow.cn',
            multiline=False,
            size_hint_y=None,
            height=dp(45)
        )
        url_section.add_widget(self.api_url_input)
        layout.add_widget(url_section)
        
        # Model
        model_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        model_section.add_widget(Label(text="Model:", size_hint_y=None, height=dp(25)))
        models = [
            'Qwen/Qwen2.5-7B-Instruct',
            'Qwen/Qwen2.5-14B-Instruct',
            'Qwen/Qwen2.5-32B-Instruct',
            'deepseek-ai/DeepSeek-V2.5',
        ]
        current_model = self.app.config_store.get('settings')['model'] if self.app.config_store.exists('settings') else models[0]
        self.model_spinner = Spinner(
            text=current_model,
            values=models,
            size_hint_y=None,
            height=dp(45)
        )
        model_section.add_widget(self.model_spinner)
        layout.add_widget(model_section)
        
        # Auto translate
        auto_section = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        auto_section.add_widget(Label(text="Auto Monitor:", size_hint_x=0.7))
        self.auto_switch = Switch(
            active=self.app.config_store.get('settings').get('auto_translate', True) if self.app.config_store.exists('settings') else True,
            size_hint_x=0.3
        )
        auto_section.add_widget(self.auto_switch)
        layout.add_widget(auto_section)
        
        # Target language
        lang_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(80))
        lang_section.add_widget(Label(text="Target:", size_hint_y=None, height=dp(25)))
        languages = ['Chinese', 'English', 'Japanese']
        current_lang = self.app.config_store.get('settings').get('target_lang', 'Chinese') if self.app.config_store.exists('settings') else 'Chinese'
        self.lang_spinner = Spinner(
            text=current_lang,
            values=languages,
            size_hint_y=None,
            height=dp(45)
        )
        lang_section.add_widget(self.lang_spinner)
        layout.add_widget(lang_section)
        
        layout.add_widget(BoxLayout(size_hint_y=0.1))
        
        # Save button
        save_btn = Button(
            text="Save",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.7, 0.3, 1)
        )
        save_btn.bind(on_press=self.save_settings)
        layout.add_widget(save_btn)
        
        self.content = layout
    
    def save_settings(self, instance):
        settings = {
            'api_key': self.api_key_input.text,
            'api_url': self.api_url_input.text,
            'model': self.model_spinner.text,
            'auto_translate': self.auto_switch.active,
            'target_lang': self.lang_spinner.text
        }
        self.app.config_store.put('settings', **settings)
        self.app.update_translator_config()
        self.dismiss()


class ScrollableLabel(ScrollView):
    """Scrollable text display widget"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_widget = TextInput(
            multiline=True,
            readonly=True,
            background_color=(0.15, 0.18, 0.15, 1),
            foreground_color=(0.9, 1.0, 0.9, 1),
            hint_text="Translation appears here...",
            size_hint_y=None
        )
        self.text_widget.bind(minimum_height=self.text_widget.setter('height'))
        self.add_widget(self.text_widget)
    
    @property
    def text(self):
        return self.text_widget.text
    
    @text.setter
    def text(self, value):
        self.text_widget.text = value
        # Scroll to top when new text is set
        self.scroll_y = 1


class TranslatorWidget(BoxLayout):
    """Main translator interface"""
    
    is_monitoring = BooleanProperty(False)
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(8)
        self.last_clipboard = ""
        
        with self.canvas.before:
            Color(0.12, 0.12, 0.15, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(15)])
        self.bind(pos=self._update_bg, size=self._update_bg)
        
        self._build_ui()
    
    def _update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def _build_ui(self):
        # Title bar
        title_bar = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        title_bar.add_widget(Label(
            text="Zotero Translator",
            font_size=dp(20),
            size_hint_x=0.6,
            color=(0.9, 0.85, 0.7, 1)
        ))
        
        settings_btn = Button(text="Set", size_hint_x=0.2, background_color=(0.3, 0.3, 0.35, 1))
        settings_btn.bind(on_press=self.open_settings)
        title_bar.add_widget(settings_btn)
        
        self.monitor_btn = Button(text="Start", size_hint_x=0.2, background_color=(0.2, 0.6, 0.3, 1))
        self.monitor_btn.bind(on_press=self.toggle_monitoring)
        title_bar.add_widget(self.monitor_btn)
        
        self.add_widget(title_bar)
        
        # Status
        self.status_label = Label(
            text="Stopped",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14),
            color=(0.7, 0.7, 0.7, 1)
        )
        self.add_widget(self.status_label)
        
        # Source area
        source_section = BoxLayout(orientation='vertical', size_hint_y=0.30)
        source_header = BoxLayout(size_hint_y=None, height=dp(30))
        source_header.add_widget(Label(text="Source:", size_hint_x=0.7, color=(0.8, 0.8, 0.9, 1)))
        paste_btn = Button(text="Paste", size_hint_x=0.3, background_color=(0.4, 0.4, 0.5, 1))
        paste_btn.bind(on_press=self.paste_text)
        source_header.add_widget(paste_btn)
        source_section.add_widget(source_header)
        
        self.source_input = TextInput(
            multiline=True,
            background_color=(0.18, 0.18, 0.22, 1),
            foreground_color=(0.95, 0.95, 0.95, 1),
            hint_text="Paste text here..."
        )
        source_section.add_widget(self.source_input)
        self.add_widget(source_section)
        
        # Translate button
        translate_btn = Button(
            text="Translate",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.25, 0.5, 0.8, 1),
            font_size=dp(18)
        )
        translate_btn.bind(on_press=self.manual_translate)
        self.add_widget(translate_btn)
        
        # Translation area - scrollable
        trans_section = BoxLayout(orientation='vertical', size_hint_y=0.50)
        trans_header = BoxLayout(size_hint_y=None, height=dp(30))
        trans_header.add_widget(Label(text="Translation:", size_hint_x=0.5, color=(0.8, 0.9, 0.8, 1)))
        
        scroll_top_btn = Button(text="Top", size_hint_x=0.25, background_color=(0.3, 0.4, 0.5, 1))
        scroll_top_btn.bind(on_press=self.scroll_to_top)
        trans_header.add_widget(scroll_top_btn)
        
        copy_btn = Button(text="Copy", size_hint_x=0.25, background_color=(0.4, 0.5, 0.4, 1))
        copy_btn.bind(on_press=self.copy_translation)
        trans_header.add_widget(copy_btn)
        trans_section.add_widget(trans_header)
        
        # Use ScrollableLabel for translation output
        self.trans_output = ScrollableLabel()
        trans_section.add_widget(self.trans_output)
        self.add_widget(trans_section)
    
    def scroll_to_top(self, instance):
        """Scroll translation to top"""
        self.trans_output.scroll_y = 1
    
    def open_settings(self, instance):
        popup = SettingsPopup(self.app)
        popup.open()
    
    def toggle_monitoring(self, instance):
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.monitor_btn.text = "Stop"
            self.monitor_btn.background_color = (0.8, 0.4, 0.2, 1)
            self.status_label.text = "Monitoring clipboard..."
            self.status_label.color = (0.3, 0.9, 0.3, 1)
            self.clipboard_event = Clock.schedule_interval(self.check_clipboard, 0.8)
            
            # Start foreground service for background monitoring
            self.app.foreground_service.start()
            
            vibrate(50)
            show_toast("Monitoring started - runs in background")
        else:
            self.monitor_btn.text = "Start"
            self.monitor_btn.background_color = (0.2, 0.6, 0.3, 1)
            self.status_label.text = "Stopped"
            self.status_label.color = (0.7, 0.7, 0.7, 1)
            if hasattr(self, 'clipboard_event'):
                self.clipboard_event.cancel()
            
            # Stop foreground service
            self.app.foreground_service.stop()
            
            vibrate(50)
            show_toast("Monitoring stopped")
    
    def check_clipboard(self, dt):
        try:
            current = Clipboard.paste()
            if current and current != self.last_clipboard and len(current.strip()) > 0:
                self.last_clipboard = current
                self.source_input.text = current
                
                # Notify user that new text was detected
                self.status_label.text = "New text detected!"
                vibrate(30)
                show_toast("Text detected, translating...")
                
                # Update notification
                self.app.foreground_service.update_notification("Translating...")
                
                if self.app.config_store.exists('settings'):
                    if self.app.config_store.get('settings').get('auto_translate', True):
                        self.do_translate(current)
        except:
            pass
    
    def paste_text(self, instance):
        try:
            text = Clipboard.paste()
            if text:
                self.source_input.text = text
                self.status_label.text = "Text pasted"
        except:
            pass
    
    def manual_translate(self, instance):
        text = self.source_input.text.strip()
        if text:
            self.do_translate(text)
    
    def do_translate(self, text):
        self.trans_output.text = "Translating..."
        self.status_label.text = "Translating, please wait..."
        self.status_label.color = (1.0, 0.8, 0.2, 1)
        
        def translate_thread():
            try:
                result = self.app.translator.translate(text)
                Clock.schedule_once(lambda dt: self.update_translation(result), 0)
            except Exception as e:
                Clock.schedule_once(lambda dt: self.update_translation(f"Error: {e}"), 0)
        
        thread = threading.Thread(target=translate_thread)
        thread.daemon = True
        thread.start()
    
    def update_translation(self, result):
        self.trans_output.text = result
        
        # Notify user that translation is complete
        vibrate(100)
        show_toast("Translation complete!")
        
        # Update notification
        self.app.foreground_service.update_notification("Translation done! Monitoring...")
        
        if self.is_monitoring:
            self.status_label.text = "Done! Monitoring..."
            self.status_label.color = (0.3, 0.9, 0.3, 1)
        else:
            self.status_label.text = "Translation complete"
            self.status_label.color = (0.3, 0.9, 0.3, 1)
    
    def copy_translation(self, instance):
        try:
            text = self.trans_output.text
            if text:
                Clipboard.copy(text)
                self.status_label.text = "Copied to clipboard!"
                vibrate(30)
                show_toast("Copied!")
        except:
            pass


class ZoteroTranslatorApp(App):
    """Main application"""
    
    def build(self):
        self.title = "Zotero Translator"
        
        # Setup Chinese font for Android
        self._setup_font()
        
        self.config_store = JsonStore('translator_config.json')
        self.translator = TranslatorService()
        self.update_translator_config()
        self.floating_bubble = FloatingBubble()
        self.foreground_service = AndroidForegroundService()
        
        if platform not in ('android', 'ios'):
            Window.size = (400, 700)
        
        self.main_widget = TranslatorWidget(self)
        return self.main_widget
    
    def _setup_font(self):
        """Setup Chinese font"""
        try:
            from kivy.core.text import LabelBase
            import os
            
            # Android system fonts
            font_paths = [
                '/system/fonts/NotoSansCJK-Regular.ttc',
                '/system/fonts/NotoSansSC-Regular.otf',
                '/system/fonts/DroidSansFallback.ttf',
            ]
            
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        LabelBase.register(name='Roboto', fn_regular=font_path)
                        print(f"Font registered: {font_path}")
                        return
                except:
                    continue
        except Exception as e:
            print(f"Font setup skipped: {e}")
    
    def update_translator_config(self):
        if self.config_store.exists('settings'):
            settings = self.config_store.get('settings')
            self.translator.set_config(
                api_key=settings.get('api_key', ''),
                api_url=settings.get('api_url', 'https://api.siliconflow.cn'),
                model=settings.get('model', 'Qwen/Qwen2.5-7B-Instruct'),
                target_lang=settings.get('target_lang', 'Chinese')
            )
    
    def on_pause(self):
        """App going to background - keep monitoring"""
        return True
    
    def on_resume(self):
        """App coming back to foreground"""
        pass


if __name__ == '__main__':
    ZoteroTranslatorApp().run()
