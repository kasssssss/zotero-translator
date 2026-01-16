# Zotero 翻译助手 - 技术文档

## 项目概述

**Zotero 翻译助手** 是一款基于 Python + Kivy 开发的 Android 应用，旨在帮助用户在平板上阅读 Zotero 文献时快速翻译外文内容。核心特点是**悬浮球功能**——用户在其他应用中复制文本后，点击悬浮球即可在不切换应用的情况下获得翻译结果。

### 核心功能

| 功能              | 描述                                |
| ----------------- | ----------------------------------- |
| 📋 **剪贴板监控** | 自动检测复制的文本并翻译            |
| 🫧 **悬浮球**      | 浮动在其他应用上方，点击触发翻译    |
| 🌐 **API 翻译**   | 调用 SiliconFlow API 进行高质量翻译 |
| 🔔 **通知提醒**   | 振动 + Toast 提示翻译状态           |
| 📱 **后台服务**   | 支持后台运行并监控剪贴板            |
| ⚙️ **灵活配置**   | 支持自定义 API、模型、目标语言      |

---

## 技术架构

### 技术栈

| 组件             | 技术                           | 说明                         |
| ---------------- | ------------------------------ | ---------------------------- |
| UI 框架          | Kivy 2.x                       | Python 跨平台 UI 框架        |
| Android 打包     | Buildozer + python-for-android | 将 Python 应用打包为 APK     |
| Android 原生调用 | PyJNIus                        | Python 调用 Android Java API |
| Android 视图     | WindowManager + Overlay        | 悬浮窗实现                   |
| API 调用         | urllib (标准库)                | HTTP 请求                    |
| 配置存储         | Kivy JsonStore                 | JSON 格式本地存储            |

### 项目结构

```
zotero_tools/
├── main.py                     # 主应用入口 (~1650 行)
├── floating_bubble.py          # 悬浮球模块 (独立实现，可替换 main.py 中的实现)
├── android_utils.py            # Android 工具函数
├── translator.py               # 翻译服务模块 (120 行)
├── buildozer.spec              # Android 打包配置
├── translator_config.json      # 用户配置存储 (运行时生成)
├── requirements.txt            # Python 依赖
├── src/
│   └── android/
│       ├── extra_manifest.xml              # AndroidManifest 补充配置
│       └── org/zotero/zoterotranslator/
│           └── ClipboardBridgeActivity.java # 透明 Activity (剪贴板读取)
├── services/                   # 服务模块 (备用实现)
│   ├── __init__.py
│   ├── floating_service.py
│   └── clipboard_service.py
├── TECHNICAL_DOC.md            # 本文档
└── README.md                   # 项目说明
```

---

## 核心架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Android 系统                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Zotero    │    │ 悬浮球      │    │ ClipboardBridge     │  │
│  │   (前台)    │    │ (Overlay)   │    │ Activity (透明)     │  │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘  │
│         │                  │                       │             │
│         │ 复制文本         │ 点击                  │ 读取剪贴板  │
│         ▼                  ▼                       ▼             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  SharedPreferences                        │   │
│  │              (跨进程通信：剪贴板文本传递)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Main Python App                        │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │   │
│  │  │TranslatorWidget│ │FloatingBubble│  │TranslatorService│  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 剪贴板读取方案对比

Android 10+ 对后台应用访问剪贴板有严格限制。本项目实现了两种方案：

| 方案                       | 实现                           | 优点                     | 缺点               |
| -------------------------- | ------------------------------ | ------------------------ | ------------------ |
| **透明 Activity** (主方案) | `ClipboardBridgeActivity.java` | 用户几乎无感知，体验最佳 | 需要编译 Java 代码 |
| **Fallback 模式** (备用)   | 主 Activity 到前台读取         | 无需额外 Java 代码       | 有明显界面切换     |

---

## 核心模块详解

### 1. FloatingBubble 类 (悬浮球)

#### 1.1 位置和文件

悬浮球实现位于 `main.py` 第 200-820 行（主实现），备用独立实现在 `floating_bubble.py`。

#### 1.2 类结构

```python
class FloatingBubble:
    """Android 悬浮球，支持拖拽和点击翻译"""

    def __init__(self):
        self.is_showing = False           # 是否正在显示
        self.is_expanded = False          # 翻译面板是否展开
        self.window_manager = None        # Android WindowManager
        self.bubble_view = None           # 悬浮球 TextView
        self.panel_view = None            # 翻译面板 ScrollView
        self.bubble_params = None         # 悬浮球布局参数
        self.panel_params = None          # 面板布局参数
        self.density = 1.0                # 屏幕密度

        # 触摸追踪
        self.initial_x = 0
        self.initial_y = 0
        self.initial_touch_x = 0
        self.initial_touch_y = 0

        # 透明 Activity 通信
        self.pending_request_id = None    # 等待响应的请求 ID
        self.pending_clipboard_read = False  # Fallback 模式标志
```

#### 1.3 核心方法

| 方法                         | 功能                              |
| ---------------------------- | --------------------------------- |
| `show(status)`               | 显示悬浮球                        |
| `hide()`                     | 隐藏悬浮球                        |
| `update_status(status)`      | 更新状态（数字/颜色）             |
| `show_translation(text)`     | 显示翻译结果面板                  |
| `_handle_click()`            | 处理点击事件                      |
| `_poll_clipboard_result(dt)` | 轮询 SharedPreferences 获取剪贴板 |

#### 1.4 状态数字说明

悬浮球通过数字显示当前状态，便于调试：

| 状态       | 显示 | 颜色         | 含义                  |
| ---------- | ---- | ------------ | --------------------- |
| `idle`     | `T`  | 蓝色 #2196F3 | 空闲状态              |
| `step1`    | `1`  | 橙色 #FF9800 | 点击已响应            |
| `step2`    | `2`  | 黄色 #FFC107 | 正在启动透明 Activity |
| `step3`    | `3`  | 绿色 #4CAF50 | 收到剪贴板内容        |
| `step4`    | `4`  | 紫色 #9C27B0 | 正在调用 API 翻译     |
| `step5`    | `5`  | 青色 #00BCD4 | 正在渲染面板          |
| `done`     | `OK` | 绿色 #4CAF50 | 翻译完成              |
| `fallback` | `F`  | 粉色 #E91E63 | 使用 Fallback 模式    |
| `error`    | `E`  | 红色 #F44336 | 发生错误              |

#### 1.5 触摸处理

使用 PythonJavaClass 实现 `OnTouchListener`：

```python
class BubbleTouchListener(PythonJavaClass):
    __javainterfaces__ = ['android/view/View$OnTouchListener']
    __javacontext__ = 'app'

    @java_method('(Landroid/view/View;Landroid/view/MotionEvent;)Z')
    def onTouch(self, view, event):
        action = event.getAction()

        if action == MotionEvent.ACTION_DOWN:
            # 记录初始位置
            self.bubble_ref.initial_x = self.bubble_ref.bubble_params.x
            self.bubble_ref.initial_touch_x = event.getRawX()
            self.is_dragging = False
            return True

        elif action == MotionEvent.ACTION_MOVE:
            dx = event.getRawX() - self.bubble_ref.initial_touch_x
            # 如果移动超过阈值，视为拖拽
            if abs(dx) > self.click_threshold:
                self.is_dragging = True
                # 更新悬浮球位置
                self.bubble_ref.bubble_params.x = int(self.bubble_ref.initial_x + dx)
                self.bubble_ref.window_manager.updateViewLayout(...)

        elif action == MotionEvent.ACTION_UP:
            if not self.is_dragging:
                # 点击事件 - 触发翻译
                self.bubble_ref._handle_click()
```

---

### 2. ClipboardBridgeActivity (透明 Activity)

#### 2.1 位置

`src/android/org/zotero/zoterotranslator/ClipboardBridgeActivity.java`

#### 2.2 作用

Android 10+ 对后台应用访问剪贴板有严格限制。只有**当前获得输入焦点的前台 Activity** 才能读取剪贴板。透明 Activity 方案：

1. 悬浮球点击时启动此 Activity
2. Activity 是透明的，用户几乎看不到
3. 在 `onWindowFocusChanged(true)` 时读取剪贴板
4. 将内容写入 SharedPreferences
5. 立即 `finish()` 返回原应用
6. Python 轮询 SharedPreferences 获取内容

#### 2.3 关键代码

```java
public class ClipboardBridgeActivity extends Activity {

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);

        if (!hasFocus || hasReadClipboard) return;
        hasReadClipboard = true;

        // 延迟 150ms 确保焦点稳定
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            // 读取剪贴板
            ClipboardManager cm = (ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
            ClipData clip = cm.getPrimaryClip();
            String text = clip.getItemAt(0).coerceToText(this).toString();

            // 写入 SharedPreferences
            SharedPreferences sp = getSharedPreferences("zoterotranslator", MODE_PRIVATE);
            sp.edit()
              .putString("clip_text", text)
              .putString("clip_request_id", requestId)
              .apply();

            // 立即关闭
            finish();
            overridePendingTransition(0, 0);  // 无动画
        }, 150);
    }
}
```

#### 2.4 Manifest 配置

`src/android/extra_manifest.xml`：

```xml
<application>
    <activity
        android:name="org.zotero.zoterotranslator.ClipboardBridgeActivity"
        android:exported="false"
        android:theme="@android:style/Theme.Translucent.NoTitleBar"
        android:noHistory="true"
        android:excludeFromRecents="true"
        android:launchMode="singleTask"
        android:taskAffinity=""
        android:finishOnTaskLaunch="true"/>
</application>
```

---

### 3. Fallback 模式

当透明 Activity 启动失败时（例如类未编译进 APK），系统自动切换到 Fallback 模式。

#### 3.1 流程

```
1. 悬浮球点击
2. 尝试启动 ClipboardBridgeActivity → 失败
3. 启动主 Activity 到前台（用户会看到界面切换）
4. 主 Activity 在 on_resume 中读取剪贴板
5. 立即返回后台（减少界面停留时间）
6. 后台翻译完成，显示悬浮球面板
```

#### 3.2 关键代码

```python
# main.py - _handle_click
try:
    # 尝试透明 Activity
    intent.setClassName(activity.getPackageName(),
                       "org.zotero.zoterotranslator.ClipboardBridgeActivity")
    activity.startActivity(intent)
except Exception:
    # Fallback: 使用主 Activity
    self.update_status("fallback")
    intent = activity.getIntent()
    intent.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)
    activity.startActivity(intent)
    self.pending_clipboard_read = True

# main.py - on_resume
def on_resume(self):
    if self.floating_bubble.pending_clipboard_read:
        self.floating_bubble.pending_clipboard_read = False
        Clock.schedule_once(self._read_clipboard_and_translate, 0.3)

# main.py - _read_clipboard_and_translate
def _read_clipboard_and_translate(self, dt):
    clipboard_text = read_clipboard()
    # 立即回到原应用，在后台翻译并通过悬浮窗显示结果
    self._go_to_background_now()
    self.floating_bubble._start_background_translation(clipboard_text)
```

---

### 4. TranslatorService 类

#### 4.1 位置

`translator.py`

#### 4.2 功能

- 调用 SiliconFlow API 进行翻译
- 支持配置 API Key、URL、Model、目标语言
- 处理网络错误和 API 错误

#### 4.3 SSL 配置

```python
# 禁用 SSL 证书验证以兼容 Android
self.ssl_context = ssl.create_default_context()
self.ssl_context.check_hostname = False
self.ssl_context.verify_mode = ssl.CERT_NONE
```

#### 4.4 API 调用

```python
def _call_api(self, system_prompt, user_prompt):
    payload = {
        "model": self.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4096
    }

    with urllib.request.urlopen(request, context=self.ssl_context, timeout=60) as response:
        result = json.loads(response.read())
        return result['choices'][0]['message']['content']
```

---

### 5. TranslatorWidget 类

#### 5.1 位置

`main.py` 第 1051-1460 行

#### 5.2 功能

主界面组件，包含：

- 标题栏（设置按钮、开始/停止按钮、悬浮球按钮）
- 状态标签
- 原文输入区域
- 翻译按钮
- 译文显示区域（可滚动）
- 复制按钮

#### 5.3 剪贴板监控

```python
def toggle_monitoring(self, instance):
    if self.is_monitoring:
        # 每 0.8 秒检查一次剪贴板
        self.clipboard_event = Clock.schedule_interval(self.check_clipboard, 0.8)
        self.app.foreground_service.start()
    else:
        Clock.unschedule(self.clipboard_event)
        self.app.foreground_service.stop()
```

#### 5.4 翻译执行（多线程）

```python
def do_translate(self, text):
    self.is_translating = True
    self.app.floating_bubble.update_status("step4")

    def translate_thread():
        try:
            result = self.app.translator.translate(text)
            self.app.floating_bubble.update_status("step5")
            Clock.schedule_once(lambda dt: self.update_translation(result), 0)
        except Exception as e:
            self.app.floating_bubble.update_status("error")
            Clock.schedule_once(lambda dt: self.update_translation(f"Error: {e}"), 0)

    thread = threading.Thread(target=translate_thread)
    thread.daemon = True
    thread.start()
```

---

### 6. ZoteroTranslatorApp 类

#### 6.1 位置

`main.py` 第 1474-1653 行

#### 6.2 功能

Kivy App 主类，负责：

- 初始化配置存储
- 初始化翻译服务
- 初始化悬浮球
- 设置中文字体
- 处理应用生命周期

#### 6.3 中文字体设置

```python
def _setup_font(self):
    font_paths = [
        '/system/fonts/NotoSansCJK-Regular.ttc',
        '/system/fonts/NotoSansSC-Regular.otf',
        '/system/fonts/DroidSansFallback.ttf',
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            LabelBase.register(name='Roboto', fn_regular=font_path)
            return
```

---

## Buildozer 配置详解

### 关键配置项

`buildozer.spec`：

```ini
# 应用信息
title = Zotero Translator
package.name = zoterotranslator
package.domain = org.zotero

# Python 依赖
requirements = python3,kivy,pyjnius,android,certifi,urllib3,cython==0.29.36

# Android 权限
android.permissions = INTERNET,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,VIBRATE,READ_CLIPBOARD,WRITE_CLIPBOARD

# Android 版本
android.api = 33
android.minapi = 21
android.ndk = 25b

# 屏幕方向
orientation = portrait,portrait-reverse,landscape,landscape-reverse

# Java 源码
android.add_src = src/android

# Manifest 补充
android.extra_manifest_xml = ./src/android/extra_manifest.xml

# CPU 架构
android.archs = arm64-v8a, armeabi-v7a
```

### 权限说明

| 权限                                 | 用途         |
| ------------------------------------ | ------------ |
| `INTERNET`                           | 调用翻译 API |
| `SYSTEM_ALERT_WINDOW`                | 显示悬浮窗   |
| `FOREGROUND_SERVICE`                 | 后台服务     |
| `VIBRATE`                            | 振动反馈     |
| `READ_CLIPBOARD` / `WRITE_CLIPBOARD` | 剪贴板操作   |

---

## 打包流程

### 环境要求

- Linux 系统（或 WSL / Google Colab）
- Python 3.8-3.10
- Java JDK 17

### 打包命令

```bash
# 1. 安装依赖
pip install buildozer cython==0.29.36

# 2. 安装系统依赖 (Ubuntu/Debian)
sudo apt-get install -y build-essential git openjdk-17-jdk \
    autoconf libtool pkg-config zlib1g-dev libncurses5-dev \
    cmake libffi-dev libssl-dev

# 3. 打包 Debug 版 APK
BUILDOZER_WARN_ON_ROOT=0 buildozer android debug

# 4. APK 输出位置
# bin/zoterotranslator-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

### Google Colab 打包

```python
# 安装依赖
!pip install buildozer cython==0.29.36
!apt-get install -y build-essential git openjdk-17-jdk

# 复制项目到无空格路径
!cp -r "/content/drive/MyDrive/zotero_tools" "/content/zotero_tools"
%cd /content/zotero_tools

# 清理缓存（如有问题）
!rm -rf .buildozer

# 打包
import os
os.environ['BUILDOZER_WARN_ON_ROOT'] = '0'
!buildozer android debug

# 下载 APK
from google.colab import files
files.download('bin/*.apk')
```

---

## 常见问题排查

### 1. 悬浮球显示 `F` (Fallback)

**原因**：透明 Activity 启动失败

**解决方案**：

1. 确认 `src/android/` 目录结构正确
2. 确认 `buildozer.spec` 中 `android.add_src = src/android` 已启用
3. 确认 `android.extra_manifest_xml = ./src/android/extra_manifest.xml` 已启用
4. 删除 `.buildozer` 目录后重新打包

### 2. 悬浮球卡在数字 `4`

**原因**：API 调用有问题

**排查步骤**：

1. 检查网络连接
2. 检查 API Key 是否配置正确
3. 切回主应用查看翻译输出框是否有错误信息

### 3. 翻译完成但面板不显示

**原因**：早期版本在回到后台后，翻译结果回调依赖 Kivy 主线程/Clock，可能导致悬浮窗更新时机不稳定

**已优化**：翻译结果显示改为直接通过悬浮窗模块在后台更新，Fallback 模式也可以立即返回原应用

### 4. 中文显示为方块

**原因**：系统字体路径不同

**解决方案**：代码中已实现多个字体路径回退，如仍有问题可将字体文件打包到 APK

### 5. 打包失败：路径包含空格

**原因**：python-for-android 不支持空格路径

**解决方案**：将项目复制到无空格路径，如 `/content/zotero_tools`

---

## 重构指南

### 1. 悬浮球模块化

当前 `FloatingBubble` 在 `main.py` 中有完整实现（约 600 行）。可以将其移动到独立的 `floating_bubble.py`：

```python
# floating_bubble.py
from kivy.utils import platform
from kivy.clock import Clock
from kivy.app import App

class FloatingBubble:
    # ... 完整实现

# main.py
from floating_bubble import FloatingBubble
```

### 2. Android 工具模块化

将 `vibrate()`, `show_toast()`, `AndroidForegroundService` 等移动到 `android_utils.py`：

```python
# android_utils.py
def vibrate(duration=50): ...
def show_toast(message): ...
class AndroidForegroundService: ...

# main.py
from android_utils import vibrate, show_toast, AndroidForegroundService
```

### 3. 翻译服务扩展

如需支持其他翻译 API，可以使用策略模式：

```python
class TranslatorBase:
    def translate(self, text, target_lang): ...

class SiliconFlowTranslator(TranslatorBase): ...
class OpenAITranslator(TranslatorBase): ...
class GoogleTranslator(TranslatorBase): ...
```

---

## API 配置说明

### SiliconFlow API

- **Base URL**: `https://api.siliconflow.cn`
- **Endpoint**: `/v1/chat/completions`
- **认证方式**: Bearer Token

### 支持的模型

| 模型 ID                     | 说明             |
| --------------------------- | ---------------- |
| `Qwen/Qwen2.5-7B-Instruct`  | 通义千问 2.5 7B  |
| `Qwen/Qwen2.5-14B-Instruct` | 通义千问 2.5 14B |
| `Qwen/Qwen2.5-32B-Instruct` | 通义千问 2.5 32B |
| `deepseek-ai/DeepSeek-V2.5` | DeepSeek V2.5    |

---

## 开发调试

### PC 端测试

```bash
pip install kivy pillow
python main.py
```

注意：悬浮球功能仅在 Android 上可用。

### Android 日志查看

```bash
adb logcat | grep -E "(python|FloatingBubble|Bubble|TranslateThread)"
```

### 状态监控

观察悬浮球显示的数字/字母变化：

```
T → 1 → 2 → 3 → 4 → 5 → OK   (透明 Activity 方案成功)
T → 1 → 2 → F → 4 → 5 → OK   (Fallback 模式成功)
T → 1 → 2 → F → 4 → E        (翻译失败)
```

---

## 版本历史

| 版本  | 日期       | 更新内容                                   |
| ----- | ---------- | ------------------------------------------ |
| 1.0.0 | 2026-01-12 | 初始版本，基础翻译功能                     |
| 1.1.0 | 2026-01-13 | 添加悬浮球功能                             |
| 1.2.0 | 2026-01-14 | 实现透明 Activity 方案，优化 Fallback 模式 |

---

## 许可证

MIT License
