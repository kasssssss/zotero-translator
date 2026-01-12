"""
下载开源中文字体 (Noto Sans SC)
运行此脚本下载字体文件
"""

import urllib.request
import os

# 使用阿里云CDN的思源黑体
FONT_URL = "https://cdn.jsdelivr.net/gh/ArkEcosystem/fonts@master/noto-sans-sc/NotoSansSC-Regular.otf"
FONT_FILE = "NotoSansSC-Regular.otf"

def download_font():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(script_dir, FONT_FILE)
    
    if os.path.exists(font_path):
        print(f"Font already exists: {font_path}")
        return font_path
    
    print(f"Downloading font from {FONT_URL}...")
    try:
        urllib.request.urlretrieve(FONT_URL, font_path)
        print(f"Font downloaded: {font_path}")
        return font_path
    except Exception as e:
        print(f"Download failed: {e}")
        print("\nPlease manually download a Chinese font and save it as:")
        print(f"  {font_path}")
        print("\nRecommended fonts:")
        print("  - Noto Sans SC: https://fonts.google.com/noto/specimen/Noto+Sans+SC")
        print("  - Source Han Sans: https://github.com/adobe-fonts/source-han-sans")
        return None

if __name__ == '__main__':
    download_font()

