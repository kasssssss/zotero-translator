"""
生成应用图标和启动画面
运行此脚本生成基础图标文件
"""

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("请先安装Pillow: pip install Pillow")
    exit(1)

import os


def create_icon(size=512):
    """创建应用图标"""
    # 创建圆角矩形图标
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 背景渐变色 (深蓝绿色)
    for y in range(size):
        r = int(25 + (y/size) * 20)
        g = int(100 + (y/size) * 50)
        b = int(120 + (y/size) * 30)
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))
    
    # 绘制圆角遮罩
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    corner_radius = size // 5
    mask_draw.rounded_rectangle(
        [(0, 0), (size-1, size-1)],
        radius=corner_radius,
        fill=255
    )
    img.putalpha(mask)
    
    # 添加书本图标符号
    draw = ImageDraw.Draw(img)
    
    # 书本形状
    book_margin = size // 6
    book_left = book_margin
    book_right = size - book_margin
    book_top = size // 4
    book_bottom = size - size // 5
    
    # 书脊
    spine_x = size // 2
    draw.rectangle(
        [(spine_x - 10, book_top), (spine_x + 10, book_bottom)],
        fill=(255, 255, 255, 200)
    )
    
    # 左页
    draw.polygon([
        (book_left, book_top + 20),
        (spine_x - 15, book_top),
        (spine_x - 15, book_bottom),
        (book_left, book_bottom - 20)
    ], fill=(255, 255, 255, 180))
    
    # 右页
    draw.polygon([
        (book_right, book_top + 20),
        (spine_x + 15, book_top),
        (spine_x + 15, book_bottom),
        (book_right, book_bottom - 20)
    ], fill=(255, 255, 255, 180))
    
    # 翻译符号 (A→中)
    try:
        # 尝试使用系统字体
        font_size = size // 8
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # 在底部添加"译"字标识
    text_y = book_bottom + 10
    draw.text(
        (size // 2, text_y),
        "译",
        fill=(255, 255, 255, 230),
        anchor="mt"
    )
    
    return img


def create_presplash(width=1080, height=1920):
    """创建启动画面"""
    img = Image.new('RGB', (width, height), (20, 30, 40))
    draw = ImageDraw.Draw(img)
    
    # 渐变背景
    for y in range(height):
        r = int(20 + (y/height) * 15)
        g = int(30 + (y/height) * 30)
        b = int(40 + (y/height) * 40)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # 中心图标
    icon = create_icon(256)
    icon_x = (width - 256) // 2
    icon_y = (height - 256) // 2 - 100
    img.paste(icon, (icon_x, icon_y), icon)
    
    # 应用名称
    try:
        title_font = ImageFont.truetype("arial.ttf", 60)
        subtitle_font = ImageFont.truetype("arial.ttf", 30)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    draw.text(
        (width // 2, icon_y + 300),
        "Zotero翻译助手",
        fill=(255, 255, 255),
        anchor="mt",
        font=title_font
    )
    
    draw.text(
        (width // 2, icon_y + 380),
        "学术文献阅读翻译工具",
        fill=(180, 180, 180),
        anchor="mt",
        font=subtitle_font
    )
    
    # 底部加载提示
    draw.text(
        (width // 2, height - 150),
        "Loading...",
        fill=(120, 120, 120),
        anchor="mt",
        font=subtitle_font
    )
    
    return img


def main():
    """生成图标文件"""
    assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    
    # 生成应用图标
    print("生成应用图标...")
    icon = create_icon(512)
    icon_path = os.path.join(assets_dir, 'icon.png')
    icon.save(icon_path, 'PNG')
    print(f"  已保存: {icon_path}")
    
    # 生成启动画面
    print("生成启动画面...")
    presplash = create_presplash()
    presplash_path = os.path.join(assets_dir, 'presplash.png')
    presplash.save(presplash_path, 'PNG')
    print(f"  已保存: {presplash_path}")
    
    print("\n✅ 图标生成完成!")
    print("提示: 如需自定义图标，请替换 assets/ 目录下的图片文件")


if __name__ == '__main__':
    main()

