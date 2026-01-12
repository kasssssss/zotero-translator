# Zotero 翻译助手 - 技术文档

## 项目概述

**Zotero 翻译助手** 是一款基于 Python + Kivy 开发的 Android 应用，旨在帮助用户在平板上阅读 Zotero 文献时快速翻译外文内容。

### 核心功能

- 📋 **剪贴板监控** - 自动检测复制的文本
- 🌐 **API 翻译** - 调用 SiliconFlow API 进行高质量翻译
- 🔔 **通知提醒** - 振动 + Toast 提示翻译状态
- 📱 **前台服务** - 支持后台监控剪贴板
- ⚙️ **灵活配置** - 支持自定义 API、模型、目标语言

---

## 技术架构

### 技术栈

| 组件             | 技术                           | 说明                         |
| ---------------- | ------------------------------ | ---------------------------- |
| UI 框架          | Kivy 2.x                       | Python 跨平台 UI 框架        |
| Android 打包     | Buildozer + python-for-android | 将 Python 应用打包为 APK     |
| Android 原生调用 | PyJNIus                        | Python 调用 Android Java API |
| API 调用         | urllib (标准库)                | HTTP 请求                    |
| 配置存储         | Kivy JsonStore                 | JSON 格式本地存储            |

### 项目结构

```
zotero_tools/
├── main.py                 # 主应用入口 (628 行)
├── translator.py           # 翻译服务模块 (120 行)
├── buildozer.spec          # Android 打包配置
├── translator_config.json  # 用户配置存储 (运行时生成)
├── requirements.txt        # Python 依赖
├── services/               # 服务模块 (备用)
│   ├── __init__.py
│   ├── floating_service.py
│   └── clipboard_service.py
├── assets/                 # 资源文件
│   └── download_font.py    # 字体下载脚本
└── TECHNICAL_DOC.md        # 本文档
```

---

## 核心模块详解

### 1. main.py - 主应用模块

#### 1.1 Android 工具函数

```python
def vibrate(duration=100):
    """设备振动 (仅 Android)"""
    # 使用 PyJNIus 调用 Android Vibrator 服务
    from jnius import autoclass
    vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
    vibrator.vibrate(duration)

def show_toast(message):
    """显示 Toast 消息 (仅 Android)"""
    # 使用 @run_on_ui_thread 装饰器确保在 UI 线程执行
    Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
```

#### 1.2 AndroidForegroundService 类

用于创建 Android 前台服务，在通知栏显示持续通知。

**关键实现：**

- 创建 NotificationChannel (Android 8.0+ 必需)
- 构建 Notification 并设置为 ongoing
- 支持动态更新通知内容

```python
class AndroidForegroundService:
    def start(self):
        # 创建通知渠道
        channel = NotificationChannel(channel_id, "Zotero Translator", IMPORTANCE_LOW)

        # 构建通知
        builder = NotificationBuilder(context, channel_id)
        builder.setContentTitle("Zotero Translator")
        builder.setContentText("Monitoring clipboard...")
        builder.setOngoing(True)  # 持续通知

        # 显示通知
        nm.notify(notification_id, notification)
```

#### 1.3 ScrollableLabel 类

解决长文本翻译结果无法滚动的问题。

```python
class ScrollableLabel(ScrollView):
    def __init__(self):
        self.text_widget = TextInput(size_hint_y=None)
        # 关键：绑定 minimum_height 实现自动高度
        self.text_widget.bind(minimum_height=self.text_widget.setter('height'))
```

#### 1.4 TranslatorWidget 类

主界面组件，包含：

- 标题栏 (设置按钮、开始/停止按钮)
- 状态标签
- 原文输入区域
- 翻译按钮
- 译文显示区域 (可滚动)

**剪贴板监控实现：**

```python
def toggle_monitoring(self, instance):
    if self.is_monitoring:
        # 每 0.8 秒检查一次剪贴板
        self.clipboard_event = Clock.schedule_interval(self.check_clipboard, 0.8)
        # 启动前台服务
        self.app.foreground_service.start()

def check_clipboard(self, dt):
    current = Clipboard.paste()
    if current != self.last_clipboard:
        self.last_clipboard = current
        self.do_translate(current)
```

**翻译执行：**

```python
def do_translate(self, text):
    def translate_thread():
        result = self.app.translator.translate(text)
        # 使用 Clock.schedule_once 确保在主线程更新 UI
        Clock.schedule_once(lambda dt: self.update_translation(result), 0)

    thread = threading.Thread(target=translate_thread)
    thread.start()
```

#### 1.5 ZoteroTranslatorApp 类

Kivy App 主类，负责：

- 初始化配置存储
- 初始化翻译服务
- 设置中文字体
- 处理应用生命周期

**中文字体设置：**

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

### 2. translator.py - 翻译服务模块

#### 2.1 TranslatorService 类

负责调用 SiliconFlow API 进行翻译。

**SSL 配置：**

```python
# 禁用 SSL 证书验证以兼容 Android
self.ssl_context = ssl.create_default_context()
self.ssl_context.check_hostname = False
self.ssl_context.verify_mode = ssl.CERT_NONE
```

**API 调用：**

```python
def _call_api(self, system_prompt, user_prompt):
    payload = {
        "model": self.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,  # 低温度保证翻译稳定性
        "max_tokens": 4096
    }

    with urllib.request.urlopen(request, context=self.ssl_context, timeout=60) as response:
        result = json.loads(response.read())
        return result['choices'][0]['message']['content']
```

**翻译提示词：**

```python
def _build_system_prompt(self):
    return f"""You are a professional academic translator.
    Translate the given text to {self.target_lang}.

    Rules:
    1. Accurate translation preserving academic terminology
    2. Natural and fluent output
    3. Keep professional terms, add original in brackets if needed
    4. Maintain paragraph structure
    5. Output translation only, no explanations"""
```

---

### 3. buildozer.spec - 打包配置

#### 关键配置项

| 配置项                | 值                                                                   | 说明                     |
| --------------------- | -------------------------------------------------------------------- | ------------------------ |
| `requirements`        | `python3,kivy,pyjnius,android,certifi,urllib3,cython==0.29.36`       | Python 依赖              |
| `android.permissions` | `INTERNET,FOREGROUND_SERVICE,VIBRATE,READ_CLIPBOARD,WRITE_CLIPBOARD` | Android 权限             |
| `android.api`         | `33`                                                                 | 目标 Android API 版本    |
| `android.minapi`      | `21`                                                                 | 最低支持 Android 5.0     |
| `orientation`         | `portrait,portrait-reverse,landscape,landscape-reverse`              | 支持横竖屏               |
| `p4a.bootstrap`       | `sdl2`                                                               | 使用 SDL2 作为 Kivy 后端 |
| `android.archs`       | `arm64-v8a, armeabi-v7a`                                             | 支持的 CPU 架构          |

---

## 打包流程

### 环境要求

- Linux 系统 (或 WSL / Google Colab)
- Python 3.8-3.10
- Java JDK 17

### 打包步骤

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

# 上传项目 zip 并解压
from google.colab import files
uploaded = files.upload()
!unzip -o *.zip

# 打包
%cd zotero_tools
import os
os.environ['BUILDOZER_WARN_ON_ROOT'] = '0'
!buildozer android debug

# 下载 APK
files.download('bin/*.apk')
```

---

## 已知问题与限制

### 1. 后台剪贴板监控受限 ⚠️

**问题描述：**
Android 10+ 对后台应用访问剪贴板有严格限制。即使使用前台服务，应用在后台时也可能无法读取剪贴板内容。

**现象：**

- 应用在前台时，剪贴板监控正常工作
- 切换到其他应用后，需要切回翻译应用才能触发翻译

**原因：**
Android 安全策略限制后台应用访问剪贴板，防止恶意应用窃取敏感信息。

**解决方案：**

1. **分屏模式** (推荐) - 将翻译应用和 Zotero 分屏显示，两者都在前台
2. **使用 Android 分享功能** - 从 Zotero 选择文本后分享到翻译应用 (待实现)
3. **使用无障碍服务** - 需要用户手动授权 (复杂，不推荐)

### 2. 中文字体显示

**问题描述：**
不同 Android 设备的系统字体路径可能不同，可能导致中文显示为方块。

**解决方案：**
代码中已实现多个字体路径回退：

```python
font_paths = [
    '/system/fonts/NotoSansCJK-Regular.ttc',
    '/system/fonts/NotoSansSC-Regular.otf',
    '/system/fonts/DroidSansFallback.ttf',
]
```

如仍有问题，可以将字体文件打包到 APK 中。

### 3. SSL 证书验证

**问题描述：**
Android 上使用 Python 标准库进行 HTTPS 请求时，可能遇到 SSL 证书验证失败。

**解决方案：**
当前代码禁用了 SSL 证书验证：

```python
self.ssl_context.check_hostname = False
self.ssl_context.verify_mode = ssl.CERT_NONE
```

⚠️ **安全提示：** 这会降低安全性，仅适用于可信的 API 服务器。

### 4. 首次打包时间长

**问题描述：**
首次使用 Buildozer 打包需要下载 Android SDK、NDK 并编译依赖，耗时约 20-60 分钟。

**解决方案：**
后续打包会复用缓存，只需 2-5 分钟。

---

## API 配置说明

### SiliconFlow API

- **Base URL**: `https://api.siliconflow.cn`
- **Endpoint**: `/v1/chat/completions`
- **认证方式**: Bearer Token

### 支持的模型

| 模型 ID                     | 说明                  |
| --------------------------- | --------------------- |
| `Qwen/Qwen2.5-7B-Instruct`  | 通义千问 2.5 7B 版本  |
| `Qwen/Qwen2.5-14B-Instruct` | 通义千问 2.5 14B 版本 |
| `Qwen/Qwen2.5-32B-Instruct` | 通义千问 2.5 32B 版本 |
| `deepseek-ai/DeepSeek-V2.5` | DeepSeek V2.5         |

---

## 未来改进方向

1. **实现 Android 分享功能** - 接收其他应用分享的文本
2. **添加翻译历史记录** - 保存历史翻译供查阅
3. **支持 OCR 图片翻译** - 截图后识别文字并翻译
4. **优化 UI 设计** - 更现代化的界面风格
5. **添加多语言自动检测** - 自动识别源语言
6. **实现真正的 Android Service** - 使用 Java 编写后台服务

---

## 开发调试

### PC 端测试

```bash
# 安装依赖
pip install kivy pillow

# 运行
python main.py
```

### Android 日志查看

```bash
# 连接设备后查看 Python 日志
adb logcat | grep python
```

---

## 许可证

MIT License

---

## 版本历史

| 版本  | 日期       | 更新内容                   |
| ----- | ---------- | -------------------------- |
| 1.0.0 | 2026-01-12 | 初始版本，实现基础翻译功能 |
