"""
悬浮球服务模块 - Android平台专用
提供后台悬浮球功能，显示翻译状态
"""

from kivy.utils import platform


class FloatingBubble:
    """悬浮球基类/占位类"""
    
    def __init__(self):
        self.is_showing = False
    
    def check_overlay_permission(self):
        return True
    
    def request_overlay_permission(self):
        pass
    
    def show(self, status=""):
        print(f"[FloatingBubble] Show: {status}")
        self.is_showing = True
    
    def hide(self):
        print("[FloatingBubble] Hide")
        self.is_showing = False
    
    def update_status(self, status):
        print(f"[FloatingBubble] Status: {status}")


# Android 平台特定实现
if platform == 'android':
    try:
        from jnius import autoclass, cast
        from android.runnable import run_on_ui_thread
        
        # Android类
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        WindowManager = autoclass('android.view.WindowManager')
        LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
        PixelFormat = autoclass('android.graphics.PixelFormat')
        Gravity = autoclass('android.view.Gravity')
        TextView = autoclass('android.widget.TextView')
        View = autoclass('android.view.View')
        AndroidColor = autoclass('android.graphics.Color')
        GradientDrawable = autoclass('android.graphics.drawable.GradientDrawable')
        Build = autoclass('android.os.Build')
        Settings = autoclass('android.provider.Settings')
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        
        
        class AndroidFloatingBubble(FloatingBubble):
            """Android悬浮球实现"""
            
            def __init__(self):
                super().__init__()
                self.activity = PythonActivity.mActivity
                self.window_manager = None
                self.floating_view = None
                self.layout_params = None
            
            def check_overlay_permission(self):
                """检查悬浮窗权限"""
                if Build.VERSION.SDK_INT >= 23:
                    return Settings.canDrawOverlays(self.activity)
                return True
            
            def request_overlay_permission(self):
                """请求悬浮窗权限"""
                if Build.VERSION.SDK_INT >= 23:
                    intent = Intent(
                        Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        Uri.parse(f"package:{self.activity.getPackageName()}")
                    )
                    self.activity.startActivityForResult(intent, 1234)
            
            @run_on_ui_thread
            def show(self, status="monitoring"):
                """显示悬浮球"""
                if not self.check_overlay_permission():
                    self.request_overlay_permission()
                    return
                
                if self.is_showing:
                    self.update_status(status)
                    return
                
                try:
                    self.window_manager = self.activity.getSystemService(Context.WINDOW_SERVICE)
                    
                    # 创建悬浮视图
                    self.floating_view = TextView(self.activity)
                    self.floating_view.setText("T")
                    self.floating_view.setTextSize(20)
                    self.floating_view.setGravity(Gravity.CENTER)
                    self.floating_view.setTextColor(AndroidColor.WHITE)
                    
                    # 设置圆形背景
                    background = GradientDrawable()
                    background.setShape(GradientDrawable.OVAL)
                    background.setColor(AndroidColor.parseColor("#4CAF50"))
                    self.floating_view.setBackground(background)
                    
                    # 设置布局参数
                    if Build.VERSION.SDK_INT >= 26:
                        layout_type = LayoutParams.TYPE_APPLICATION_OVERLAY
                    else:
                        layout_type = LayoutParams.TYPE_PHONE
                    
                    self.layout_params = LayoutParams(
                        120, 120,
                        layout_type,
                        LayoutParams.FLAG_NOT_FOCUSABLE,
                        PixelFormat.TRANSLUCENT
                    )
                    self.layout_params.gravity = Gravity.TOP | Gravity.LEFT
                    self.layout_params.x = 0
                    self.layout_params.y = 200
                    
                    self.window_manager.addView(self.floating_view, self.layout_params)
                    self.is_showing = True
                    
                except Exception as e:
                    print(f"Show floating bubble failed: {e}")
            
            @run_on_ui_thread
            def hide(self):
                """隐藏悬浮球"""
                if self.is_showing and self.floating_view and self.window_manager:
                    try:
                        self.window_manager.removeView(self.floating_view)
                        self.is_showing = False
                        self.floating_view = None
                    except Exception as e:
                        print(f"Hide floating bubble failed: {e}")
            
            @run_on_ui_thread
            def update_status(self, status):
                """更新状态"""
                if self.floating_view:
                    try:
                        bg = self.floating_view.getBackground()
                        if status == "translating":
                            self.floating_view.setText("...")
                            if bg:
                                bg.setColor(AndroidColor.parseColor("#FFC107"))
                        elif status == "error":
                            self.floating_view.setText("!")
                            if bg:
                                bg.setColor(AndroidColor.parseColor("#F44336"))
                        else:
                            self.floating_view.setText("T")
                            if bg:
                                bg.setColor(AndroidColor.parseColor("#4CAF50"))
                    except Exception as e:
                        print(f"Update status failed: {e}")
        
        # 使用 Android 实现替换基类
        FloatingBubble = AndroidFloatingBubble
        
    except Exception as e:
        print(f"Android floating service init failed: {e}")
        # 保持使用基类 FloatingBubble
