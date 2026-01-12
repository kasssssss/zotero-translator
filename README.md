# 📚 Zotero 翻译助手

一款专为学术文献阅读设计的 Android 翻译工具，帮助你在平板上更高效地使用 Zotero 阅读外文文献。

## ✨ 功能特性

- 🔄 **剪贴板监控** - 自动检测复制的文本并翻译
- 🌐 **SiliconFlow API** - 使用高质量大语言模型进行翻译
- 🔮 **悬浮球** - 后台运行时显示状态指示
- 📱 **后台服务** - 支持后台持续监控
- ⚙️ **灵活配置** - 支持自定义 API、模型和目标语言

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装Python依赖
pip install -r requirements.txt

# Linux/macOS需要额外安装
pip install buildozer
sudo apt-get install -y python3-pip build-essential git openjdk-17-jdk
```

### 2. 配置 API

1. 访问 [SiliconFlow](https://siliconflow.cn) 注册账号
2. 获取 API Key
3. 在应用设置中填入 API Key

### 3. 桌面端测试

```bash
# 在PC上运行测试
python main.py
```

### 4. 打包 Android APK

```bash
# 初始化buildozer (首次)
buildozer init

# 打包debug版APK
buildozer android debug

# 打包release版APK
buildozer android release
```

## 📁 项目结构

```
zotero_tools/
├── main.py                 # 主应用入口
├── translator.py           # 翻译服务模块
├── services/
│   ├── __init__.py
│   ├── floating_service.py # 悬浮球服务
│   └── clipboard_service.py # 剪贴板监控
├── assets/
│   ├── icon.png           # 应用图标
│   └── presplash.png      # 启动画面
├── buildozer.spec         # Android打包配置
├── requirements.txt       # Python依赖
└── README.md
```

## ⚙️ 配置说明

### 支持的模型

| 模型                      | 说明                  |
| ------------------------- | --------------------- |
| Qwen/Qwen2.5-7B-Instruct  | 通义千问 2.5 7B 版本  |
| Qwen/Qwen2.5-14B-Instruct | 通义千问 2.5 14B 版本 |
| Qwen/Qwen2.5-32B-Instruct | 通义千问 2.5 32B 版本 |
| deepseek-ai/DeepSeek-V2.5 | DeepSeek V2.5         |
| THUDM/glm-4-9b-chat       | 智谱 GLM-4            |

### API 参数

- **Base URL**: `https://api.siliconflow.cn`
- **Endpoint**: `/v1/chat/completions`
- **认证方式**: Bearer Token

## 🔧 Android 权限说明

应用需要以下权限：

| 权限                | 用途         |
| ------------------- | ------------ |
| INTERNET            | 访问翻译 API |
| SYSTEM_ALERT_WINDOW | 显示悬浮球   |
| FOREGROUND_SERVICE  | 后台服务     |
| READ_CLIPBOARD      | 读取剪贴板   |

## 📱 使用流程

1. **安装 APK** - 在 Android 设备上安装打包好的 APK
2. **配置 API** - 进入设置，填入 SiliconFlow API Key
3. **选择模型** - 选择翻译模型和目标语言
4. **开始监控** - 点击播放按钮开启剪贴板监控
5. **阅读文献** - 在 Zotero 中复制需要翻译的文本
6. **查看翻译** - 应用会自动翻译并显示结果

## 🐛 常见问题

### Q: 悬浮球不显示？

A: 需要在系统设置中授予"悬浮窗"权限

### Q: 翻译失败？

A: 检查 API Key 是否正确，网络是否连通

### Q: 后台被杀？

A: 在系统设置中将应用加入电池优化白名单

## 🔨 开发说明

### 在 WSL 中打包

如果在 Windows 上开发，建议使用 WSL 打包：

```bash
# 在WSL中
cd /mnt/e/Files/daimaxuexi/zotero_tools
pip install buildozer
buildozer android debug
```

### 调试日志

```bash
# 查看Android日志
adb logcat | grep python
```

## 📄 许可证

MIT License

## 🙏 致谢

- [Kivy](https://kivy.org/) - Python 跨平台 UI 框架
- [SiliconFlow](https://siliconflow.cn/) - AI 模型 API 服务
- [Buildozer](https://buildozer.readthedocs.io/) - Android 打包工具
