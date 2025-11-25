# 流程
# 1 搞蒙版
# 2 截头像
# 3 叠头像
# 4 嵌字
# 5 改分辨率
#1 优化算法 尽量不出现两个重复表情在一块
#2 优化代码 md0.2s的时间太长了
#3 把原代码重做 他def的函数我看不懂 只能打印一次文本吗我靠
#4 增加多种表情包选择
#5 把选择的地方做的更明显一些
#6 加阴影
#7 新增：快捷键切换角色功能
#8 新增：限制生成图片大小功能

print("""角色说明:
1为樱羽艾玛，2为二阶堂希罗，3为橘雪莉，4为远野汉娜
5为夏目安安，6为月代雪，7为冰上梅露露，8为城崎诺亚，9为莲见蕾雅，10为佐伯米莉亚
11为黑部奈叶香，12为宝生玛格，13为紫藤亚里沙，14为泽渡可可

快捷键说明:
Ctrl+1 到 Ctrl+9: 切换角色1-9
Ctrl+q: 切换角色10
Ctrl+e: 切换角色11
Ctrl+r: 切换角色12
Ctrl+t: 切换角色13
Ctrl+y: 切换角色14
Ctrl+0: 显示当前角色
Alt+1-9: 切换表情1-9(部分角色表情较少 望大家谅解)
Enter: 生成图片
Esc: 退出程序
Ctrl+Tab: 清除图片

程序说明：
这个版本的程序占用体积较小，但是需要预加载，初次更换角色后需要等待数秒才能正常使用，望周知（
按Tab可清除生成图片，降低占用空间，但清除图片后需重启才能正常使用
感谢各位的支持


"""
)



# 角色配置
# 1为樱羽艾玛，2为二阶堂希罗，3为橘雪莉，4为远野汉娜
# 5为夏目安安，6为月代雪，7为冰上梅露露，8为城崎诺亚，9为莲见蕾雅，10为佐伯米莉亚
# 11为黑部奈叶香，12为宝生玛格，13为紫藤亚里沙，14为泽渡可可
current_character_index = 3  # 初始角色为橘雪莉（索引从0开始）

mahoshojo_postion = [728,355] #文本范围起始位置
mahoshojo_over = [2339,800]   #文本范围右下角位置










import io
import os
import random
import shutil
import time

import keyboard
import matplotlib
import pyperclip
import win32clipboard
from PIL import Image, ImageDraw, ImageFont, ImageOps
import io
from PIL import Image
import win32clipboard
import os
import re
import shutil

from image_fit_paste import paste_image_auto
from text_fit_draw import draw_text_auto

matplotlib.use("Agg")
import re

from matplotlib import mathtext

i = -1
value_1 = -1
expression = None

# 角色配置字典
mahoshojo = {
    "ema": {"emotion_count": 8, "font": "font3.ttf"},     # 樱羽艾玛
    "hiro": {"emotion_count": 6, "font": "font3.ttf"},    # 二阶堂希罗
    "sherri": {"emotion_count": 7, "font": "font3.ttf"},  # 橘雪莉
    "hanna": {"emotion_count": 5, "font": "font3.ttf"},   # 远野汉娜
    "anan": {"emotion_count": 9, "font": "font3.ttf"},    # 夏目安安
    "yuki" : {"emotion_count": 18, "font": "font3.ttf"},
    "meruru": {"emotion_count": 6, "font": "font3.ttf"},   # 冰上梅露露
    "noa": {"emotion_count": 6, "font": "font3.ttf"},     # 城崎诺亚
    "reia": {"emotion_count": 7, "font": "font3.ttf"},    # 莲见蕾雅
    "miria": {"emotion_count": 4, "font": "font3.ttf"},   # 佐伯米莉亚
    "nanoka": {"emotion_count": 5, "font": "font3.ttf"},  # 黑部奈叶香
    "mago": {"emotion_count": 5, "font": "font3.ttf"},   # 宝生玛格
    "alisa": {"emotion_count": 6, "font": "font3.ttf"},   # 紫藤亚里沙
    "coco": {"emotion_count": 5, "font": "font3.ttf"}
}

# 角色文字配置字典 - 每个角色对应4个文字配置
text_configs_dict = {
    "nanoka": [  # 黑部奈叶香
        {"text":"黑","position":(759,63),"font_color":(131,143,147),"font_size":196},
        {"text":"部","position":(955,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"奈","position":(1053,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"叶香","position":(1197,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "hiro": [  # 二阶堂希罗
        {"text":"二","position":(759,63),"font_color":(239,79,84),"font_size":196},
        {"text":"阶堂","position":(955,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"希","position":(1143,110),"font_color":(255, 255, 255),"font_size":147},
        {"text":"罗","position":(1283,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "ema": [  # 樱羽艾玛
        {"text":"樱","position":(759,73),"font_color":(253,145,175),"font_size":186},
        {"text":"羽","position":(949,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"艾","position":(1039,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"玛","position":(1183,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "sherri": [  # 橘雪莉
        {"text":"橘","position":(759,73),"font_color":(137,177,251),"font_size":186},
        {"text":"雪","position":(943,110),"font_color":(255, 255, 255),"font_size":147},
        {"text":"莉","position":(1093,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"","position":(0,0),"font_color":(255, 255, 255),"font_size":1}  # 占位符
    ],
    "anan": [  # 夏目安安
        {"text":"夏","position":(759,73),"font_color":(159,145,251),"font_size":186},
        {"text":"目","position":(949,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"安","position":(1039,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"安","position":(1183,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "noa": [  # 城崎诺亚
        {"text":"城","position":(759,73),"font_color":(104,223,231),"font_size":186},
        {"text":"崎","position":(945,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"诺","position":(1042,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"亚","position":(1186,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "coco": [  # 泽渡可可
        {"text":"泽","position":(759,73),"font_color":(251,114,78),"font_size":186},
        {"text":"渡","position":(945,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"可","position":(1042,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"可","position":(1186,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "alisa": [  # 紫藤亚里沙
        {"text":"紫","position":(759,73),"font_color":(235,75,60),"font_size":186},
        {"text":"藤","position":(945,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"亚","position":(1042,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"里沙","position":(1186,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "reia": [  # 莲见蕾雅
        {"text":"莲","position":(759,73),"font_color":(253,177,88),"font_size":186},
        {"text":"见","position":(945,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"蕾","position":(1042,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"雅","position":(1186,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "mago": [  # 宝生玛格
        {"text":"宝","position":(759,73),"font_color":(185,124,235),"font_size":186},
        {"text":"生","position":(945,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"玛","position":(1042,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"格","position":(1186,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "hanna": [  # 远野汉娜
        {"text":"远","position":(759,73),"font_color":(169,199,30),"font_size":186},
        {"text":"野","position":(945,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"汉","position":(1042,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"娜","position":(1186,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "meruru": [  # 冰上梅露露
        {"text":"冰","position":(759,73),"font_color":(227,185,175),"font_size":186},
        {"text":"上","position":(945,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"梅","position":(1042,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"露露","position":(1186,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "miria": [  # 佐伯米莉亚
        {"text":"佐","position":(759,73),"font_color":(235,207,139),"font_size":186},
        {"text":"伯","position":(945,175),"font_color":(255, 255, 255),"font_size":92},
        {"text":"米","position":(1042,117),"font_color":(255, 255, 255),"font_size":147},
        {"text":"莉亚","position":(1186,175),"font_color":(255, 255, 255),"font_size":92}
    ],
    "yuki": [  #月代雪
    {"text":"月","position":(759,63),"font_color":(195,209,231),"font_size":196},
    {"text":"代","position":(948,175),"font_color":(255, 255, 255),"font_size":92},
    {"text":"雪","position":(1053,117),"font_color":(255, 255, 255),"font_size":147},
    {"text":"","position":(0,0),"font_color":(255, 255, 255),"font_size":1}
        ]
}
import getpass

# 获取当前用户名
username = getpass.getuser()

# 构建用户文档路径
if os.name == 'nt':  # Windows系统
    user_documents = os.path.join('C:\\', 'Users', username, 'Documents')
else:  # 其他系统
    user_documents = os.path.expanduser('~/Documents')

# 构建\"魔裁\"文件夹路径
magic_cut_folder = os.path.join(user_documents, '魔裁')

# 创建\"魔裁\"文件夹（如果不存在）
os.makedirs(magic_cut_folder, exist_ok=True)

# 角色列表（按顺序对应1-13的角色）
character_list = list(mahoshojo.keys())

# 获取当前角色信息
def get_current_character():
    return character_list[current_character_index-1]

def get_current_font():
    # 返回完整的字体文件绝对路径
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), mahoshojo[get_current_character()]["font"])

def get_current_emotion_count():
    return mahoshojo[get_current_character()]["emotion_count"]

def delate(folder_path, quality=85):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.jpg'):
            os.remove(folder_path+"\\"+filename)


def generate_and_save_images(character_name):
    now_file = os.path.dirname(os.path.abspath(__file__))

    # 获取当前角色的表情数量
    emotion_count = mahoshojo[character_name]["emotion_count"]

    for filename in os.listdir(magic_cut_folder):
        if filename.startswith(character_name):
            return
    print("正在加载")
    for i in range(16):
        for j in range(emotion_count):
                # 使用绝对路径加载背景图片和角色图片
            background_path = os.path.join(now_file, "background", f"c{i+1}.png")
            overlay_path = os.path.join(now_file, character_name, f"{character_name} ({j+1}).png")

            background = Image.open(background_path).convert("RGBA")
            overlay = Image.open(overlay_path).convert("RGBA")

            img_num = j * 16 + i + 1
            result = background.copy()
            result.paste(overlay, (0, 134), overlay)

                # 使用绝对路径保存生成的图片
            save_path = os.path.join(os.path.join(magic_cut_folder), f"{character_name} ({img_num}).jpg")
            result.convert("RGB").save(save_path)
    print("加载完成")


def switch_character(new_index):
    global current_character_index
    if 0 <= new_index < len(character_list):
        current_character_index = new_index
        character_name = get_current_character()
        print(f"已切换到角色: {character_name}")

        # 生成并保存图片
        generate_and_save_images(character_name)

        return True
    return False

# 显示当前角色信息
def show_current_character():
    character_name = get_current_character()
    print(f"当前角色: {character_name}")


# 显示当前角色信息
show_current_character()

# 测试：生成当前角色的图片
generate_and_save_images(get_current_character())

def get_expression(i):
    global expression
    character_name = get_current_character()
    if i <= mahoshojo[character_name]["emotion_count"]:
        print(f"已切换至第{i}个表情")
        expression = i


# 随机获取表情图片名称
# 优化版本：使用循环替代递归，避免栈溢出风险
# 维护上一次选择的表情类型，确保不连续选择相同表情
def get_random_value():
    global value_1,expression
    character_name = get_current_character()
    emotion_count = get_current_emotion_count()
    total_images = 16 * emotion_count

    if expression:
        i = random.randint((expression-1)*16+1,expression*16)
        value_1 = i
        expression = None
        return f"{character_name} ({i})"

    # 循环直到找到与上次不同表情的图片
    max_attempts = 100  # 防止无限循环的安全机制
    attempts = 0

    while attempts < max_attempts:
        i = random.randint(1, total_images)
        current_emotion = (i-1) // 16

        # 处理第一次调用的情况
        if value_1 == -1:
            value_1 = i
            return f"{character_name} ({i})"

        # 检查是否与上次表情不同
        if current_emotion != (value_1-1) //16:
            value_1 = i
            return f"{character_name} ({i})"

        attempts += 1

    # 如果尝试多次仍未找到（理论上概率极低），则返回当前随机数
    # 这是一个安全机制，防止程序卡住
    value_1 = i
    return f"{character_name} ({i})"


HOTKEY= "enter"

# 全选快捷键, 此按键并不会监听, 而是会作为模拟输入
# 此值为字符串, 代表热键的键名, 格式同 HOTKEY
SELECT_ALL_HOTKEY= "ctrl+a"

# 剪切快捷键, 此按键并不会监听, 而是会作为模拟输入
# 此值为字符串, 代表热键的键名, 格式同 HOTKEY
CUT_HOTKEY= "ctrl+x"

# 黏贴快捷键, 此按键并不会监听, 而是会作为模拟输入
# 此值为字符串, 代表热键的键名, 格式同 HOTKEY
PASTE_HOTKEY= "ctrl+v"

# 发送消息快捷键, 此按键并不会监听, 而是会作为模拟输入
# 此值为字符串, 代表热键的键名, 格式同 HOTKEY
SEND_HOTKEY= "enter"

# 是否阻塞按键, 如果热键设置为阻塞模式, 则按下热键时不会将该按键传递给前台应用
# 如果生成热键和发送热键相同, 则强制阻塞, 防止误触发发送消息
# 此值为布尔值, True 或 False
BLOCK_HOTKEY= False

# 操作的间隔, 如果失效可以适当增大此数值
# 此值为数字, 单位为秒
DELAY= 0.1

# 是否自动黏贴生成的图片(如果为否则保留图片在剪贴板, 可以手动黏贴)
# 此值为布尔值, True 或 False
AUTO_PASTE_IMAGE= True

# 生成图片后是否自动发送(模拟回车键输入), 只有开启自动黏贴才生效
# 此值为布尔值, True 或 False
AUTO_SEND_IMAGE= True



def copy_png_bytes_to_clipboard(png_bytes: bytes):
    # 打开 PNG 字节为 Image
    image = Image.open(io.BytesIO(png_bytes))
    # 转换成 BMP 字节流（去掉 BMP 文件头的前 14 个字节）
    with io.BytesIO() as output:
        image.convert("RGB").save(output, "BMP")
        bmp_data = output.getvalue()[14:]
    # 打开剪贴板并写入 DIB 格式
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
    win32clipboard.CloseClipboard()


def cut_all_and_get_text() -> str:
    """
    #模拟 Ctrl+A / Ctrl+X 剪切全部文本，并返回剪切得到的内容。
    #delay: 每步之间的延时（秒），默认0.1秒。
    """
    # 备份原剪贴板
    old_clip = pyperclip.paste()

    # 清空剪贴板，防止读到旧数据
    pyperclip.copy("")

    # 发送 Ctrl+A 和 Ctrl+X
    keyboard.send(SELECT_ALL_HOTKEY)
    keyboard.send(CUT_HOTKEY)
    time.sleep(DELAY)

    # 获取剪切后的内容
    new_clip = pyperclip.paste()

    return new_clip

def try_get_image() -> Image.Image | None:
    """
    尝试从剪贴板获取图像，如果没有图像则返回 None。
    仅支持 Windows。
    """
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
            if data:
                # 将 DIB 数据转换为字节流，供 Pillow 打开
                bmp_data = data
                # DIB 格式缺少 BMP 文件头，需要手动加上
                # BMP 文件头是 14 字节，包含 "BM" 标识和文件大小信息
                header = b'BM' + (len(bmp_data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                image = Image.open(io.BytesIO(header + bmp_data))
                return image
    except Exception as e:
        print("无法从剪贴板获取图像：", e)
    finally:
        try:
            win32clipboard.CloseClipboard()
        except:
            pass
    return None

def render_latex_to_image(
    expr: str,
    color=(255, 255, 255),
    dpi=200,
    target_height: int | None = None,
) -> Image.Image | None:
    """
    使用 matplotlib.mathtext 渲染 LaTeX，生成指定颜色、可缩放的透明贴图。
    target_height 用于把公式高度缩放到与字号一致。
    """
    buffer = io.BytesIO()
    try:
        mathtext.math_to_image(f"${expr}$", buffer, dpi=dpi, color="#000000", format="png")
    except Exception as exc:
        print("LaTeX 渲染失败:", exc)
        return None

    buffer.seek(0)
    gray = Image.open(buffer).convert("L")
    alpha = ImageOps.invert(gray)
    colored = Image.new("RGBA", gray.size, color + (0,))
    colored.putalpha(alpha)

    if target_height and colored.height > 0:
        scale = target_height / colored.height
        if scale > 0:
            new_width = max(1, int(round(colored.width * scale)))
            new_height = max(1, int(round(colored.height * scale)))
            if new_width != colored.width or new_height != colored.height:
                colored = colored.resize((new_width, new_height), Image.LANCZOS)

    return colored

LATEX_PATTERN = re.compile(r"(\${1,2})(.+?)\1", re.DOTALL)
def split_rich_text(raw: str):
    """
    返回 [{"type": "text", "value": "普通文字"}, {"type": "latex", "value": r"\frac{1}{2}"}...]
    """
    parts = []
    last = 0
    for match in LATEX_PATTERN.finditer(raw):
        if match.start() > last:
            parts.append({"type": "text", "value": raw[last:match.start()]})
        parts.append({"type": "latex", "value": match.group(2)})
        last = match.end()
    if last < len(raw):
        parts.append({"type": "text", "value": raw[last:]})
    return parts

def render_richtext_to_image(
    segments, font_path, font_size, max_width, color=(255, 255, 255), line_spacing=10
):
    font = ImageFont.truetype(font_path, font_size)
    lines = []
    current_line = []
    current_width = 0
    line_height = 0
    for seg in segments:
        if seg["type"] == "text":
            text = seg["value"]
            if not text:
                continue
            bbox = font.getbbox(text)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            block = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(block).text(
                (-bbox[0], -bbox[1]), text, font=font, fill=color
            )
        else:
            block = render_latex_to_image(
                seg["value"], color=color, target_height=font_size
            )
            if block is None:
                continue
            w, h = block.size
        if current_width + w > max_width and current_line:
            lines.append((current_line, line_height))
            current_line = []
            current_width = 0
            line_height = 0
        current_line.append((block, current_width))
        current_width += w
        line_height = max(line_height, h)
    if current_line:
        lines.append((current_line, line_height))
    if not lines:
        return None
    total_height = sum(h for _, h in lines) + line_spacing * (len(lines) - 1)
    canvas = Image.new("RGBA", (max_width, total_height), (0, 0, 0, 0))
    y = 0
    for line, height in lines:
        for block, x in line:
            canvas.alpha_composite(block, (x, y))
        y += height + line_spacing
    return canvas

def Start():
    print("Start generate...")

    character_name = get_current_character()
    address = os.path.join(magic_cut_folder, get_random_value()+".jpg")
    BASEIMAGE_FILE = address
    print(character_name,str(1+(value_1//16)),"背景",str(value_1%16))



# 文本框左上角坐标 (x, y), 同时适用于图片框
# 此值为一个二元组, 例如 (100, 150), 单位像素, 图片的左上角记为 (0, 0)
    TEXT_BOX_TOPLEFT= (mahoshojo_postion[0], mahoshojo_postion[1])
# 文本框右下角坐标 (x, y), 同时适用于图片框
# 此值为一个二元组, 例如 (100, 150), 单位像素, 图片的左上角记为 (0, 0)
    IMAGE_BOX_BOTTOMRIGHT= (mahoshojo_over[0], mahoshojo_over[1])
    text=cut_all_and_get_text()
    image=try_get_image()

    if text == "" and image is None:
        print("no text or image")
        return

    png_bytes=None
    max_width = IMAGE_BOX_BOTTOMRIGHT[0]-TEXT_BOX_TOPLEFT[0]


    if image is not None:
        try:
            print("Get image")
            png_bytes = paste_image_auto(
                image_source=BASEIMAGE_FILE,
                image_overlay=None,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                content_image=image,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True,
                keep_alpha=True,      # 使用内容图 alpha 作为蒙版
                role_name=character_name,  # 传递角色名称
                text_configs_dict=text_configs_dict,  # 传递文字配置字典
                )
        except Exception as e:
            print("Generate image failed:", e)
            return

    elif text != "":
        segments = split_rich_text(text)
        has_latex = any(segment["type"] == "latex" for segment in segments)
        if has_latex:
            try:
                rich_image = render_richtext_to_image(segments,
                font_path=get_current_font(),
                font_size=145,
                max_width=max_width,
                color=(255, 255, 255),
                line_spacing=12,
                )
            except Exception as e:
                print("Generate image failed:", e)
                return
            if rich_image is not None:
                image = rich_image
                text = ""
            png_bytes = paste_image_auto(
                image_source=BASEIMAGE_FILE,
                image_overlay=None,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                content_image=image,
                align="center",
                valign="middle",
                padding=12,
                allow_upscale=True,
                keep_alpha=True,      # 使用内容图 alpha 作为蒙版
                role_name=character_name,  # 传递角色名称
                text_configs_dict=text_configs_dict,  # 传递文字配置字典
                )
        else:
    
    elif text != "":
        print("Get text: "+text)
# ==================== 新增功能开始 ====================
        # 定义高亮规则变量，默认为 None
        highlight_args = {}
        
        # 如果当前角色是夏目安安 (anan)
        if character_name == "anan":
            # 使用正则表达式匹配中文方括号及内容
            # 颜色采用安安的主题紫色 (参考自你的 text_configs_dict)
            highlight_args = {
                "bracket_color": (159, 145, 251)  # 安安的紫色
            }
        # ==================== 新增功能结束 ====================
        try:
            png_bytes = draw_text_auto(
                image_source=BASEIMAGE_FILE,
                image_overlay=None,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                text=text,
                align="left",
                valign='top' ,
                color=(255, 255, 255),
                max_font_height=145,        # 例如限制最大字号高度为 145 像素
                font_path=get_current_font(),
                role_name=character_name,  # 传递角色名称
                text_configs_dict=text_configs_dict,  # 传递文字配置字典
                **highlight_args
                )
            if png_bytes is not None:
                return png_bytes
    if png_bytes is None:
        print("Generate image failed")
        return
    copy_png_bytes_to_clipboard(png_bytes)
    if AUTO_PASTE_IMAGE:
        keyboard.send(PASTE_HOTKEY)
        time.sleep(0.3)
        if AUTO_SEND_IMAGE:
            keyboard.send(HOTKEY)

# 角色切换快捷键绑定
# 按Ctrl+1 到 Ctrl+9: 切换角色1-9
for i in range(1,10):
    keyboard.add_hotkey(f'ctrl+{i}', lambda idx=i: switch_character(idx))

# 角色10-13使用特殊快捷键
keyboard.add_hotkey('ctrl+q', lambda: switch_character(10))   # 角色10
keyboard.add_hotkey('ctrl+e', lambda: switch_character(11))  # 角色11
keyboard.add_hotkey('ctrl+r', lambda: switch_character(12))  # 角色12
keyboard.add_hotkey('ctrl+t', lambda: switch_character(13))  # 角色13
keyboard.add_hotkey('ctrl+y', lambda: switch_character(0))
keyboard.add_hotkey('ctrl+Tab', lambda: delate(magic_cut_folder))

for i in range(1,10):
    keyboard.add_hotkey(f'alt+{i}', lambda idx=i: get_expression(idx))

# 绑定 Ctrl+Alt+H 作为全局热键
ok=keyboard.add_hotkey(HOTKEY,Start, suppress=BLOCK_HOTKEY or HOTKEY==SEND_HOTKEY)

# 绑定Ctrl+0显示当前角色
keyboard.add_hotkey('ctrl+0', show_current_character)

# 保持程序运行
keyboard.wait("Esc")
