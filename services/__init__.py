"""
服务模块初始化
"""

try:
    from .floating_service import FloatingBubble
except Exception as e:
    print(f"FloatingBubble import failed: {e}")
    class FloatingBubble:
        def __init__(self): self.is_showing = False
        def show(self, status=""): pass
        def hide(self): pass

try:
    from .clipboard_service import ClipboardService, AndroidClipboardService
except Exception as e:
    print(f"ClipboardService import failed: {e}")
    class ClipboardService:
        def __init__(self, callback=None): pass
    AndroidClipboardService = ClipboardService

__all__ = ['FloatingBubble', 'ClipboardService', 'AndroidClipboardService']
