"""
剪贴板监控服务
"""

from kivy.utils import platform
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard


class ClipboardService:
    """剪贴板服务基类"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.last_text = ""
        self.is_running = False
        self.monitor_event = None
    
    def get_clipboard_text(self):
        """获取剪贴板文本"""
        try:
            return Clipboard.paste() or ""
        except Exception as e:
            print(f"Get clipboard failed: {e}")
            return ""
    
    def check_clipboard_change(self, dt=None):
        """检查剪贴板变化"""
        current_text = self.get_clipboard_text()
        if current_text and current_text != self.last_text:
            self.last_text = current_text
            if self.callback:
                self.callback(current_text)
    
    def start_monitoring(self):
        """启动监控"""
        self.is_running = True
        self.monitor_event = Clock.schedule_interval(self.check_clipboard_change, 1.0)
        print("[ClipboardService] Monitoring started")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_event:
            self.monitor_event.cancel()
        print("[ClipboardService] Monitoring stopped")
    
    def show_foreground_notification(self):
        """显示前台通知（占位）"""
        pass
    
    def cancel_notification(self):
        """取消通知（占位）"""
        pass


# Android 平台使用原生剪贴板
if platform == 'android':
    try:
        from jnius import autoclass
        from android import mActivity
        
        Context = autoclass('android.content.Context')
        ClipboardManager = autoclass('android.content.ClipboardManager')
        
        class AndroidClipboardService(ClipboardService):
            """Android剪贴板服务"""
            
            def __init__(self, callback=None):
                super().__init__(callback)
                self._init_clipboard()
            
            def _init_clipboard(self):
                """初始化Android剪贴板管理器"""
                try:
                    context = mActivity.getApplicationContext()
                    self.clipboard_manager = context.getSystemService(Context.CLIPBOARD_SERVICE)
                except Exception as e:
                    print(f"Init Android clipboard failed: {e}")
                    self.clipboard_manager = None
            
            def get_clipboard_text(self):
                """获取剪贴板文本"""
                try:
                    if self.clipboard_manager:
                        clip = self.clipboard_manager.getPrimaryClip()
                        if clip and clip.getItemCount() > 0:
                            item = clip.getItemAt(0)
                            text = item.getText()
                            if text:
                                return str(text)
                except Exception as e:
                    print(f"Get Android clipboard failed: {e}")
                
                # 回退到 Kivy 剪贴板
                return super().get_clipboard_text()
        
        # 使用 Android 实现
        ClipboardService = AndroidClipboardService
        
    except Exception as e:
        print(f"Android clipboard service init failed: {e}")
        # 保持使用基类


# 别名以保持兼容性
AndroidClipboardService = ClipboardService
