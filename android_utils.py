"""
Android Utility Functions
Provides common Android operations like vibration, toast, permissions
"""

from kivy.utils import platform

if platform == 'android':
    try:
        from jnius import autoclass
        from android.runnable import run_on_ui_thread
    except ImportError:
        print("[AndroidUtils] Warning: Android imports not available")


def vibrate(duration=50):
    """Vibrate device"""
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            activity = PythonActivity.mActivity
            vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
            vibrator.vibrate(duration)
        except Exception as e:
            print(f"[Vibrate] Error: {e}")


def show_toast(message):
    """Show Android toast message"""
    if platform == 'android':
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Toast = autoclass('android.widget.Toast')
            String = autoclass('java.lang.String')
            activity = PythonActivity.mActivity
            
            @run_on_ui_thread
            def _show():
                Toast.makeText(activity, String(message), Toast.LENGTH_SHORT).show()
            _show()
        except Exception as e:
            print(f"[Toast] Error: {e}")


def check_overlay_permission():
    """Check if overlay permission is granted"""
    if platform != 'android':
        return True
    
    try:
        from jnius import autoclass
        VERSION = autoclass('android.os.Build$VERSION')
        Settings = autoclass('android.provider.Settings')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        
        if VERSION.SDK_INT >= 23:
            activity = PythonActivity.mActivity
            return Settings.canDrawOverlays(activity)
        return True
    except Exception as e:
        print(f"[Permission] Check error: {e}")
        return False


def request_overlay_permission():
    """Request overlay permission"""
    if platform != 'android':
        return
    
    try:
        from jnius import autoclass
        VERSION = autoclass('android.os.Build$VERSION')
        Settings = autoclass('android.provider.Settings')
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        
        if VERSION.SDK_INT >= 23:
            activity = PythonActivity.mActivity
            intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse(f"package:{activity.getPackageName()}")
            )
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(intent)
    except Exception as e:
        print(f"[Permission] Request error: {e}")


class AndroidForegroundService:
    """Android foreground service for background clipboard monitoring"""
    
    def __init__(self):
        self.is_running = False
    
    def start(self, title="Clipboard Monitor", message="Monitoring clipboard..."):
        """Start foreground service with notification"""
        if platform != 'android':
            return
        
        try:
            from jnius import autoclass
            PythonService = autoclass('org.kivy.android.PythonService')
            service = PythonService.mService
            
            if service:
                self.is_running = True
                print(f"[ForegroundService] Started: {title}")
        except Exception as e:
            print(f"[ForegroundService] Start error: {e}")
    
    def update_notification(self, message):
        """Update notification text"""
        if platform != 'android' or not self.is_running:
            return
        
        try:
            # Just print for now - actual notification update requires more setup
            print(f"[ForegroundService] Update: {message}")
        except Exception as e:
            print(f"[ForegroundService] Update error: {e}")
    
    def stop(self):
        """Stop foreground service"""
        if platform != 'android' or not self.is_running:
            return
        
        try:
            self.is_running = False
            print("[ForegroundService] Stopped")
        except Exception as e:
            print(f"[ForegroundService] Stop error: {e}")

