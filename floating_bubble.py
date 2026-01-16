"""
Floating Bubble Implementation for Android
Provides draggable bubble with expandable translation panel
"""

from kivy.utils import platform
from kivy.clock import Clock
from kivy.app import App

if platform == 'android':
    try:
        from jnius import autoclass, PythonJavaClass, java_method
        from android.runnable import run_on_ui_thread
    except ImportError:
        print("[FloatingBubble] Warning: Android imports not available")


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


class FloatingBubble:
    """Floating bubble for Android with expandable translation panel"""
    
    def __init__(self):
        self.is_showing = False
        self.is_expanded = False
        self.window_manager = None
        self.bubble_view = None
        self.panel_view = None
        self.bubble_params = None
        self.panel_params = None
        self.last_error = ""
        self.on_click_callback = None
        self.density = 1.0
        
        # Touch tracking for drag
        self.initial_x = 0
        self.initial_y = 0
        self.initial_touch_x = 0
        self.initial_touch_y = 0
        
        # For transparent Activity clipboard access
        self.pending_request_id = None
        self.last_processed_request_id = None
        
        # Fallback flag for main Activity clipboard access
        self.pending_clipboard_read = False
        
        # Translation result cache for fallback display
        self.cached_translation = None
        
        # Start polling for SharedPreferences results
        if platform == 'android':
            Clock.schedule_interval(self._poll_clipboard_result, 0.1)
    
    def _poll_clipboard_result(self, dt):
        """Poll SharedPreferences for clipboard result from ClipboardBridgeActivity"""
        if not self.pending_request_id:
            return
        
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            
            activity = PythonActivity.mActivity
            if not activity:
                return
            
            prefs = activity.getSharedPreferences("zoterotranslator", Context.MODE_PRIVATE)
            result_request_id = prefs.getString("clip_request_id", "")
            
            if result_request_id == self.pending_request_id:
                self.update_status("step3")
                clip_text = prefs.getString("clip_text", "")
                
                print(f"[FloatingBubble] Got clipboard: {len(clip_text)} chars")
                
                self.pending_request_id = None
                self.last_processed_request_id = result_request_id
                
                if clip_text and len(clip_text.strip()) > 0:
                    print("[FloatingBubble] Starting background translation...")
                    self._start_background_translation(clip_text)
                else:
                    show_toast("Clipboard empty")
                    self.update_status("error")
                    
        except Exception as e:
            print(f"[FloatingBubble] Poll error: {e}")
    
    def _start_background_translation(self, text):
        """Start translation in background thread"""
        import threading
        
        def translate_thread():
            try:
                app = App.get_running_app()
                if not app or not hasattr(app, 'translator'):
                    return
                
                self.update_status("step4")
                print(f"[FloatingBubble] Translating...")
                
                result = app.translator.translate(text)
                
                if result and not (result.startswith("Error:") or result.startswith("Translation failed:")):
                    print(f"[FloatingBubble] Translation done: {len(result)} chars")
                    self.cached_translation = result
                    Clock.schedule_once(lambda dt: self._show_translation_result(result), 0)
                else:
                    Clock.schedule_once(lambda dt: self._show_translation_error(result or "Empty result"), 0)
                    
            except Exception as e:
                print(f"[FloatingBubble] Translation error: {e}")
                Clock.schedule_once(lambda dt: self._show_translation_error(str(e)), 0)
        
        thread = threading.Thread(target=translate_thread)
        thread.daemon = True
        thread.start()
    
    def _show_translation_result(self, result):
        """Show translation result (called on main Kivy thread)"""
        try:
            self.update_status("step5")
            print("[FloatingBubble] Showing translation result...")
            self.show_translation(result)
            self.update_status("done")
        except Exception as e:
            print(f"[FloatingBubble] Show result error: {e}")
            self.update_status("error")
            show_toast(f"Result: {result[:80]}")
    
    def _show_translation_error(self, error):
        """Show translation error"""
        self.update_status("error")
        show_toast(f"Error: {error[:50]}")
    
    def show(self, status="idle"):
        """Show floating bubble"""
        if platform != 'android':
            self.last_error = "Not Android"
            return False
        
        if self.is_showing:
            return True
        
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            from android.runnable import run_on_ui_thread
            
            self_ref = self
            
            class BubbleTouchListener(PythonJavaClass):
                __javainterfaces__ = ['android/view/View$OnTouchListener']
                __javacontext__ = 'app'
                
                def __init__(self, bubble_ref):
                    super().__init__()
                    self.bubble_ref = bubble_ref
                    self.is_dragging = False
                    self.click_threshold = 10
                
                @java_method('(Landroid/view/View;Landroid/view/MotionEvent;)Z')
                def onTouch(self, view, event):
                    from jnius import autoclass
                    MotionEvent = autoclass('android.view.MotionEvent')
                    action = event.getAction()
                    
                    if action == MotionEvent.ACTION_DOWN:
                        self.bubble_ref.initial_x = self.bubble_ref.bubble_params.x
                        self.bubble_ref.initial_y = self.bubble_ref.bubble_params.y
                        self.bubble_ref.initial_touch_x = event.getRawX()
                        self.bubble_ref.initial_touch_y = event.getRawY()
                        self.is_dragging = False
                        return True
                    
                    elif action == MotionEvent.ACTION_MOVE:
                        dx = event.getRawX() - self.bubble_ref.initial_touch_x
                        dy = event.getRawY() - self.bubble_ref.initial_touch_y
                        
                        if abs(dx) > self.click_threshold or abs(dy) > self.click_threshold:
                            if not self.is_dragging:
                                self.is_dragging = True
                                if self.bubble_ref.is_expanded and self.bubble_ref.panel_view:
                                    try:
                                        self.bubble_ref.window_manager.removeView(self.bubble_ref.panel_view)
                                        self.bubble_ref.panel_view = None
                                        self.bubble_ref.is_expanded = False
                                    except:
                                        pass
                        
                        if self.is_dragging:
                            try:
                                new_x = int(self.bubble_ref.initial_x + dx)
                                new_y = int(self.bubble_ref.initial_y + dy)
                                new_x = max(0, new_x)
                                new_y = max(0, new_y)
                                
                                self.bubble_ref.bubble_params.x = new_x
                                self.bubble_ref.bubble_params.y = new_y
                                self.bubble_ref.window_manager.updateViewLayout(
                                    self.bubble_ref.bubble_view, 
                                    self.bubble_ref.bubble_params
                                )
                            except Exception as e:
                                print(f"[Bubble] Drag error: {e}")
                        return True
                    
                    elif action == MotionEvent.ACTION_UP:
                        if not self.is_dragging:
                            # Click detected - launch ClipboardBridgeActivity
                            print("[Bubble] Click!")
                            self.bubble_ref._handle_click()
                        return True
                    
                    return False
            
            @run_on_ui_thread
            def _show():
                try:
                    from jnius import autoclass
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    Context = autoclass('android.content.Context')
                    LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
                    PixelFormat = autoclass('android.graphics.PixelFormat')
                    Gravity = autoclass('android.view.Gravity')
                    TextView = autoclass('android.widget.TextView')
                    AndroidColor = autoclass('android.graphics.Color')
                    GradientDrawable = autoclass('android.graphics.drawable.GradientDrawable')
                    VERSION = autoclass('android.os.Build$VERSION')
                    MotionEvent = autoclass('android.view.MotionEvent')
                    
                    activity = PythonActivity.mActivity
                    self_ref.window_manager = activity.getSystemService(Context.WINDOW_SERVICE)
                    metrics = activity.getResources().getDisplayMetrics()
                    density = metrics.density
                    self_ref.density = density
                    
                    # Create bubble view
                    JavaString = autoclass('java.lang.String')
                    self_ref.bubble_view = TextView(activity)
                    self_ref.bubble_view.setText(JavaString("T"))
                    self_ref.bubble_view.setTextSize(18)
                    self_ref.bubble_view.setGravity(Gravity.CENTER)
                    self_ref.bubble_view.setTextColor(AndroidColor.parseColor("#FFFFFF"))
                    
                    # Bubble background
                    bg = GradientDrawable()
                    bg.setShape(GradientDrawable.OVAL)
                    bg.setColor(AndroidColor.parseColor("#2196F3"))
                    bg.setStroke(int(2 * density), AndroidColor.parseColor("#FFFFFF"))
                    self_ref.bubble_view.setBackground(bg)
                    
                    # Layout params
                    if VERSION.SDK_INT >= 26:
                        layout_type = LayoutParams.TYPE_APPLICATION_OVERLAY
                    else:
                        layout_type = LayoutParams.TYPE_PHONE
                    
                    bubble_size = int(56 * density)
                    self_ref.bubble_params = LayoutParams(
                        bubble_size, bubble_size,
                        layout_type,
                        LayoutParams.FLAG_NOT_FOCUSABLE,
                        PixelFormat.TRANSLUCENT
                    )
                    self_ref.bubble_params.gravity = Gravity.TOP | Gravity.LEFT
                    self_ref.bubble_params.x = int(16 * density)
                    self_ref.bubble_params.y = int(200 * density)
                    
                    # Touch listener
                    touch_listener = BubbleTouchListener(self_ref)
                    self_ref.bubble_view.setOnTouchListener(touch_listener)
                    
                    # Add to window
                    self_ref.window_manager.addView(self_ref.bubble_view, self_ref.bubble_params)
                    self_ref.is_showing = True
                    self_ref.last_error = ""
                    print("[FloatingBubble] Bubble shown!")
                    
                except Exception as e:
                    self_ref.last_error = str(e)
                    print(f"[FloatingBubble] Show error: {e}")
                    import traceback
                    traceback.print_exc()
            
            _show()
            return True
            
        except Exception as e:
            self.last_error = str(e)
            print(f"[FloatingBubble] Import error: {e}")
            return False
    
    def _handle_click(self):
        """Handle bubble click - launch transparent Activity"""
        self.update_status("step1")
        
        try:
            import time
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            Intent = autoclass('android.content.Intent')
            activity = PythonActivity.mActivity
            
            # Hide existing panel
            if self.is_expanded and self.panel_view:
                try:
                    self.window_manager.removeView(self.panel_view)
                    self.panel_view = None
                    self.is_expanded = False
                except:
                    pass
            
            # Generate request ID
            request_id = str(int(time.time() * 1000))
            self.pending_request_id = request_id
            
            # Try transparent Activity
            launched = False
            try:
                self.update_status("step2")
                intent = Intent()
                intent.setClassName(activity.getPackageName(), "org.zotero.zoterotranslator.ClipboardBridgeActivity")
                intent.putExtra("request_id", request_id)
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                intent.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION)
                activity.startActivity(intent)
                activity.overridePendingTransition(0, 0)
                launched = True
                print(f"[Bubble] Launched ClipboardBridgeActivity")
            except Exception as e:
                print(f"[Bubble] ClipboardBridgeActivity failed: {e}")
                self.update_status("fallback")
                
                # Fallback: bring main Activity to front
                try:
                    intent = activity.getIntent()
                    intent.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)
                    intent.addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
                    intent.addFlags(Intent.FLAG_ACTIVITY_NO_ANIMATION)
                    activity.startActivity(intent)
                    activity.overridePendingTransition(0, 0)
                    
                    self.pending_clipboard_read = True
                    launched = True
                    print("[Bubble] Fallback to main Activity")
                except Exception as e2:
                    print(f"[Bubble] Fallback failed: {e2}")
            
            if not launched:
                self.update_status("error")
                
        except Exception as e:
            print(f"[Bubble] Click handler error: {e}")
            self.update_status("error")
    
    def update_status(self, status):
        """Update bubble appearance"""
        if platform != 'android' or not self.bubble_view:
            return
        
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread
            
            AndroidColor = autoclass('android.graphics.Color')
            JavaString = autoclass('java.lang.String')
            self_ref = self
            status_text = status
            
            @run_on_ui_thread
            def _update():
                try:
                    bg = self_ref.bubble_view.getBackground()
                    
                    status_map = {
                        "step1": ("1", "#FF9800"),
                        "step2": ("2", "#FFC107"),
                        "step3": ("3", "#4CAF50"),
                        "step4": ("4", "#9C27B0"),
                        "step5": ("5", "#00BCD4"),
                        "translating": ("...", "#9C27B0"),
                        "done": ("OK", "#4CAF50"),
                        "fallback": ("F", "#E91E63"),
                        "error": ("E", "#F44336"),
                    }
                    
                    text, color = status_map.get(status_text, ("T", "#2196F3"))
                    self_ref.bubble_view.setText(JavaString(text))
                    if bg:
                        bg.setColor(AndroidColor.parseColor(color))
                        
                except Exception as e:
                    print(f"[Bubble] Update status error: {e}")
            
            _update()
        except Exception as e:
            print(f"[Bubble] Update import error: {e}")
    
    def show_translation(self, text):
        """Show translation in panel"""
        print(f"[Bubble] show_translation: {len(text)} chars, is_showing: {self.is_showing}")
        
        if platform != 'android' or not self.is_showing:
            show_toast(f"Result: {text[:60]}")
            return
        
        try:
            from jnius import autoclass
            from android.runnable import run_on_ui_thread
            
            self_ref = self
            translation_text = text
            
            @run_on_ui_thread
            def _show_panel():
                try:
                    from jnius import autoclass
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    Context = autoclass('android.content.Context')
                    LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
                    PixelFormat = autoclass('android.graphics.PixelFormat')
                    Gravity = autoclass('android.view.Gravity')
                    TextView = autoclass('android.widget.TextView')
                    AndroidColor = autoclass('android.graphics.Color')
                    GradientDrawable = autoclass('android.graphics.drawable.GradientDrawable')
                    VERSION = autoclass('android.os.Build$VERSION')
                    ScrollView = autoclass('android.widget.ScrollView')
                    TypedValue = autoclass('android.util.TypedValue')
                    
                    activity = PythonActivity.mActivity
                    if not activity:
                        return
                    
                    metrics = activity.getResources().getDisplayMetrics()
                    density = metrics.density
                    
                    # Remove old panel
                    if self_ref.panel_view and self_ref.window_manager:
                        try:
                            self_ref.window_manager.removeView(self_ref.panel_view)
                        except:
                            pass
                        finally:
                            self_ref.panel_view = None
                            self_ref.is_expanded = False
                    
                    # Create scroll view
                    scroll = ScrollView(activity)
                    scroll.setFillViewport(True)
                    
                    # Text view
                    JavaString = autoclass('java.lang.String')
                    text_view = TextView(activity)
                    text_view.setText(JavaString(translation_text))
                    text_view.setTextSize(TypedValue.COMPLEX_UNIT_SP, 14)
                    text_view.setTextColor(AndroidColor.parseColor("#FFFFFF"))
                    text_view.setPadding(int(12*density), int(12*density), int(12*density), int(12*density))
                    scroll.addView(text_view)
                    
                    # Background
                    panel_bg = GradientDrawable()
                    panel_bg.setCornerRadius(12 * density)
                    panel_bg.setColor(AndroidColor.parseColor("#DD333333"))
                    scroll.setBackground(panel_bg)
                    
                    self_ref.panel_view = scroll
                    
                    # Layout params
                    if VERSION.SDK_INT >= 26:
                        layout_type = LayoutParams.TYPE_APPLICATION_OVERLAY
                    else:
                        layout_type = LayoutParams.TYPE_PHONE
                    
                    panel_width = int(280 * density)
                    panel_height = int(200 * density)
                    
                    self_ref.panel_params = LayoutParams(
                        panel_width, panel_height,
                        layout_type,
                        LayoutParams.FLAG_NOT_FOCUSABLE,
                        PixelFormat.TRANSLUCENT
                    )
                    self_ref.panel_params.gravity = Gravity.TOP | Gravity.LEFT
                    
                    # Position relative to bubble
                    bubble_x = self_ref.bubble_params.x if self_ref.bubble_params else int(16 * density)
                    bubble_y = self_ref.bubble_params.y if self_ref.bubble_params else int(200 * density)
                    bubble_size = int(56 * density)
                    
                    screen_width = metrics.widthPixels
                    if bubble_x + bubble_size + panel_width + 10 < screen_width:
                        self_ref.panel_params.x = bubble_x + bubble_size + int(8 * density)
                        self_ref.panel_params.y = bubble_y
                    else:
                        self_ref.panel_params.x = max(int(8 * density), bubble_x - panel_width - int(8 * density))
                        self_ref.panel_params.y = bubble_y
                    
                    # Add to window
                    self_ref.window_manager.addView(self_ref.panel_view, self_ref.panel_params)
                    self_ref.is_expanded = True
                    print("[Bubble] Panel shown!")
                    
                except Exception as e:
                    print(f"[Bubble] Show panel error: {e}")
                    import traceback
                    traceback.print_exc()
            
            _show_panel()
            
        except Exception as e:
            print(f"[Bubble] show_translation error: {e}")
            show_toast(f"Result: {text[:80]}")
    
    def hide(self):
        """Hide bubble"""
        if platform != 'android' or not self.is_showing:
            return
        
        try:
            from android.runnable import run_on_ui_thread
            
            self_ref = self
            
            @run_on_ui_thread
            def _hide():
                try:
                    if self_ref.panel_view and self_ref.window_manager:
                        try:
                            self_ref.window_manager.removeView(self_ref.panel_view)
                        except:
                            pass
                        self_ref.panel_view = None
                        self_ref.is_expanded = False
                    
                    if self_ref.bubble_view and self_ref.window_manager:
                        try:
                            self_ref.window_manager.removeView(self_ref.bubble_view)
                        except:
                            pass
                        self_ref.bubble_view = None
                        self_ref.is_showing = False
                except Exception as e:
                    print(f"[Bubble] Hide error: {e}")
            
            _hide()
        except Exception as e:
            print(f"[Bubble] Hide import error: {e}")
