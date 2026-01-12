[app]

# (str) 应用名称
title = Zotero翻译助手

# (str) 包名
package.name = zoterotranslator

# (str) 包域名 (用于android/ios打包)
package.domain = org.zotero

# (str) 主入口点
source.dir = .

# (list) 要包含的源文件
source.include_exts = py,png,jpg,kv,atlas,json,otf,ttf,ttc

# (list) 要排除的目录
source.exclude_dirs = tests, bin, venv, .git, __pycache__, .buildozer

# (str) 应用版本
version = 1.0.0

# (list) 应用需求
requirements = python3,kivy,pyjnius,android,certifi,urllib3,cython==0.29.36

# (str) 自定义源代码用于支持requirements
# requirements.source.kivy = ../../kivy

# (str) 预设 (无或调试选项)
# presplash.filename = %(source.dir)s/assets/presplash.png

# (str) 应用图标
# icon.filename = %(source.dir)s/assets/icon.png

# (str) 支持的屏幕方向
orientation = portrait,portrait-reverse,landscape,landscape-reverse

# (list) 服务列表
# services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

# OSX 特定选项
osx.python_version = 3
osx.kivy_version = 2.2.1

# Android 特定选项
fullscreen = 0

# (bool) 是否Android应用是一个游戏
android.game = False

# (str) Android manifest中的应用主题
# android.apptheme = "@android:style/Theme.NoTitleBar"

# (list) 添加到AndroidManifest.xml的权限
android.permissions = INTERNET,SYSTEM_ALERT_WINDOW,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,VIBRATE,READ_CLIPBOARD,WRITE_CLIPBOARD

# (list) Android功能需求
# android.features = android.hardware.usb.host

# (int) 目标Android API
android.api = 33

# (int) 最小API
android.minapi = 21

# (int) Android SDK版本
android.sdk = 33

# (str) Android NDK版本
android.ndk = 25b

# (int) Android NDK API
android.ndk_api = 21

# (bool) 使用私有存储
android.private_storage = True

# (str) Android NDK目录 (如果为空, 会自动下载)
# android.ndk_path =

# (str) Android SDK目录 (如果为空, 会自动下载)
# android.sdk_path =

# (str) ANT目录 (如果为空, 会自动下载)
# android.ant_path =

# (bool) 是否跳过更新Android SDK
android.skip_update = False

# (bool) 是否接受SDK许可
android.accept_sdk_license = True

# (str) Android入口点
android.entrypoint = org.kivy.android.PythonActivity

# (str) 后台服务实现
# android.service.service_name.foreground = True

# (list) 使用gradle依赖
# android.gradle_dependencies =

# (bool) 启用AndroidX
android.enable_androidx = True

# (list) 添加Java编译选项
# android.add_compile_options = 

# (list) Gradle仓库
# android.add_gradle_repositories =

# (list) packaging options以添加到build.gradle
# android.add_packaging_options =

# (list) Java文件添加到项目
# android.add_jars =

# (list) 添加Java源文件夹
# android.add_src =

# (list) 添加AAR文件
# android.add_aars =

# (list) Gradle插件
# android.add_gradle_plugins =

# (list) Gradle类路径
# android.add_classpath =

# (str) 本地类
# android.ouya.category = GAME

# (str) OUYA意图过滤器
# android.ouya.icon.filename = %(source.dir)s/data/ouya_icon.png

# (str) manifest文件
# android.manifest.filename =

# (str) 自定义java代码
# android.add_java_sources =

# (str) p4a源代码分支
# p4a.source_dir =

# (str) 本地p4a
# p4a.local_recipes =

# (str) p4a仓库
# p4a.hook =

# (str) bootstrap
p4a.bootstrap = sdl2

# (int) p4a log级别
log_level = 2

# (int) 打包并发数
# p4a.multi_instance = False

# (str) 释放时签名的alias
# android.keyalias = my-alias

# (str) 签名存储的密码
# android.keystore_password = my-password

# (str) 签名的密码
# android.key_password = my-alias-password

# (str) 签名的keystore文件
# android.keystore = my-keystore.keystore

# (str) Android logcat过滤器
android.logcat_filters = *:S python:D

# (bool) 复制库而不是进行引用
android.copy_libs = 1

# (str) 归档格式 (apk, aab)
android.archs = arm64-v8a, armeabi-v7a

# (bool) 允许将apk备份 (True意味着允许备份)
android.allow_backup = True

# (str) 格式用于打包发布版本 (aab或apk或aar)
# android.release_artifact = aab

# (str) 格式用于打包调试版本 (apk或aar)
# android.debug_artifact = apk

#
# Python for android (p4a) 特定选项
#

# (str) python-for-android 分支
p4a.branch = master

# (str) python-for-android git克隆url
# p4a.url =

# (str) python-for-android分支或commit
# p4a.commit =

#
# iOS 特定选项
#

# (str) 开发团队的teamID
# ios.codesign.allowed =

#
# iOS/Mac OSX 特定选项
#

# (str) 依赖的Python.framework路径
# osx.python_version =

# (str) objc 类前缀
# ios.objc_prefix =

[buildozer]

# (int) 日志级别 (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) 警告模式 (0 = 显示警告; 1 = 显示所有警告)
warn_on_root = 1

# (str) Buildozer工作目录
# build_dir = ./.buildozer

# (str) Buildozer bin目录
# bin_dir = ./bin

