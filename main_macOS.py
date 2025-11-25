"""适用于 macOS 的版本"""
# todo: 整合两个版本的重复代码，减小体积

print("""角色说明:
1为樱羽艾玛，2为二阶堂希罗，3为橘雪莉，4为远野汉娜
5为夏目安安，6为月代雪，7为冰上梅露露，8为城崎诺亚，9为莲见蕾雅，10为佐伯米莉亚
11为黑部奈叶香，12为宝生玛格，13为紫藤亚里沙，14为泽渡可可

快捷键说明:
Ctrl+1 到 Ctrl+9: 切换角色1-9
Ctrl+q: 切换角色10
Ctrl+w: 切换角色11
Ctrl+e: 切换角色12
Ctrl+r: 切换角色13
Ctrl+t: 切换角色14
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

mahoshojo_postion = [728, 355]  # 文本范围起始位置
mahoshojo_over = [2339, 800]  # 文本范围右下角位置

import random
import time
from pynput import keyboard
from pynput.keyboard import Key, Controller, GlobalHotKeys
import pyperclip
import io
from PIL import Image
import pyclip
from sys import platform
import os
import tempfile
import subprocess
from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto

kbd_controller = Controller()  # 跨平台键盘控制器
PLATFORM = platform.lower()  # 获取当前平台信息
print("提示: 在 macOS 上首次运行时，请在'系统设置 > 隐私与安全性 > 辅助功能'中授权此程序")

i = -1
value_1 = -1
expression = None

# 角色配置字典
mahoshojo = {
    "ema": {"emotion_count": 8, "font": "font3.ttf"},  # 樱羽艾玛
    "hiro": {"emotion_count": 6, "font": "font3.ttf"},  # 二阶堂希罗
    "sherri": {"emotion_count": 7, "font": "font3.ttf"},  # 橘雪莉
    "hanna": {"emotion_count": 5, "font": "font3.ttf"},  # 远野汉娜
    "anan": {"emotion_count": 9, "font": "font3.ttf"},  # 夏目安安
    "yuki": {"emotion_count": 18, "font": "font3.ttf"},
    "meruru": {"emotion_count": 6, "font": "font3.ttf"},  # 冰上梅露露
    "noa": {"emotion_count": 6, "font": "font3.ttf"},  # 城崎诺亚
    "reia": {"emotion_count": 7, "font": "font3.ttf"},  # 莲见蕾雅
    "miria": {"emotion_count": 4, "font": "font3.ttf"},  # 佐伯米莉亚
    "nanoka": {"emotion_count": 5, "font": "font3.ttf"},  # 黑部奈叶香
    "mago": {"emotion_count": 5, "font": "font3.ttf"},  # 宝生玛格
    "alisa": {"emotion_count": 6, "font": "font3.ttf"},  # 紫藤亚里沙
    "coco": {"emotion_count": 5, "font": "font3.ttf"}
}

# 角色文字配置字典 - 每个角色对应4个文字配置
text_configs_dict = {
    "nanoka": [  # 黑部奈叶香
        {"text": "黑", "position": (759, 63), "font_color": (131, 143, 147), "font_size": 196},
        {"text": "部", "position": (955, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "奈", "position": (1053, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "叶香", "position": (1197, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "hiro": [  # 二阶堂希罗
        {"text": "二", "position": (759, 63), "font_color": (239, 79, 84), "font_size": 196},
        {"text": "阶堂", "position": (955, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "希", "position": (1143, 110), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "罗", "position": (1283, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "ema": [  # 樱羽艾玛
        {"text": "樱", "position": (759, 73), "font_color": (253, 145, 175), "font_size": 186},
        {"text": "羽", "position": (949, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "艾", "position": (1039, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "玛", "position": (1183, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "sherri": [  # 橘雪莉
        {"text": "橘", "position": (759, 73), "font_color": (137, 177, 251), "font_size": 186},
        {"text": "雪", "position": (943, 110), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "莉", "position": (1093, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "", "position": (0, 0), "font_color": (255, 255, 255), "font_size": 1}  # 占位符
    ],
    "anan": [  # 夏目安安
        {"text": "夏", "position": (759, 73), "font_color": (159, 145, 251), "font_size": 186},
        {"text": "目", "position": (949, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "安", "position": (1039, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "安", "position": (1183, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "noa": [  # 城崎诺亚
        {"text": "城", "position": (759, 73), "font_color": (104, 223, 231), "font_size": 186},
        {"text": "崎", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "诺", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "亚", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "coco": [  # 泽渡可可
        {"text": "泽", "position": (759, 73), "font_color": (251, 114, 78), "font_size": 186},
        {"text": "渡", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "可", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "可", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "alisa": [  # 紫藤亚里沙
        {"text": "紫", "position": (759, 73), "font_color": (235, 75, 60), "font_size": 186},
        {"text": "藤", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "亚", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "里沙", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "reia": [  # 莲见蕾雅
        {"text": "莲", "position": (759, 73), "font_color": (253, 177, 88), "font_size": 186},
        {"text": "见", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "蕾", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "雅", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "mago": [  # 宝生玛格
        {"text": "宝", "position": (759, 73), "font_color": (185, 124, 235), "font_size": 186},
        {"text": "生", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "玛", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "格", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "hanna": [  # 远野汉娜
        {"text": "远", "position": (759, 73), "font_color": (169, 199, 30), "font_size": 186},
        {"text": "野", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "汉", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "娜", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "meruru": [  # 冰上梅露露
        {"text": "冰", "position": (759, 73), "font_color": (227, 185, 175), "font_size": 186},
        {"text": "上", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "梅", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "露露", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "miria": [  # 佐伯米莉亚
        {"text": "佐", "position": (759, 73), "font_color": (235, 207, 139), "font_size": 186},
        {"text": "伯", "position": (945, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "米", "position": (1042, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "莉亚", "position": (1186, 175), "font_color": (255, 255, 255), "font_size": 92}
    ],
    "yuki": [  # 月代雪
        {"text": "月", "position": (759, 63), "font_color": (195, 209, 231), "font_size": 196},
        {"text": "代", "position": (948, 175), "font_color": (255, 255, 255), "font_size": 92},
        {"text": "雪", "position": (1053, 117), "font_color": (255, 255, 255), "font_size": 147},
        {"text": "", "position": (0, 0), "font_color": (255, 255, 255), "font_size": 1}
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
    return character_list[current_character_index - 1]


def get_current_font():
    # 返回完整的字体文件绝对路径
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), mahoshojo[get_current_character()]["font"])


def get_current_emotion_count():
    return mahoshojo[get_current_character()]["emotion_count"]


def delate(folder_path, quality=85):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.jpg'):
            os.remove(folder_path + "\\" + filename)


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
            background_path = os.path.join(now_file, "background", f"c{i + 1}.png")
            overlay_path = os.path.join(now_file, character_name, f"{character_name} ({j + 1}).png")

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
    global value_1, expression
    character_name = get_current_character()
    emotion_count = get_current_emotion_count()
    total_images = 16 * emotion_count

    if expression:
        i = random.randint((expression - 1) * 16 + 1, expression * 16)
        value_1 = i
        expression = None
        return f"{character_name} ({i})"

    # 循环直到找到与上次不同表情的图片
    max_attempts = 100  # 防止无限循环的安全机制
    attempts = 0

    while attempts < max_attempts:
        i = random.randint(1, total_images)
        current_emotion = (i - 1) // 16

        # 处理第一次调用的情况
        if value_1 == -1:
            value_1 = i
            return f"{character_name} ({i})"

        # 检查是否与上次表情不同
        if current_emotion != (value_1 - 1) // 16:
            value_1 = i
            return f"{character_name} ({i})"

        attempts += 1

    # 如果尝试多次仍未找到（理论上概率极低），则返回当前随机数
    # 这是一个安全机制，防止程序卡住
    value_1 = i
    return f"{character_name} ({i})"


# HOTKEY = "enter"
#
# # 全选快捷键, 此按键并不会监听, 而是会作为模拟输入
# # 此值为字符串, 代表热键的键名, 格式同 HOTKEY
# SELECT_ALL_HOTKEY = "ctrl+a"
#
# # 剪切快捷键, 此按键并不会监听, 而是会作为模拟输入
# # 此值为字符串, 代表热键的键名, 格式同 HOTKEY
# CUT_HOTKEY = "ctrl+x"
#
# # 黏贴快捷键, 此按键并不会监听, 而是会作为模拟输入
# # 此值为字符串, 代表热键的键名, 格式同 HOTKEY
# PASTE_HOTKEY = "ctrl+v"
#
# # 发送消息快捷键, 此按键并不会监听, 而是会作为模拟输入
# # 此值为字符串, 代表热键的键名, 格式同 HOTKEY
# SEND_HOTKEY = "enter"
#
# # 是否阻塞按键, 如果热键设置为阻塞模式, 则按下热键时不会将该按键传递给前台应用
# # 如果生成热键和发送热键相同, 則強制阻塞, 防止誤觸發發送消息
# # 此值为布尔值, True 或 False
# BLOCK_HOTKEY = False

# 操作的间隔, 如果失效可以适当增大此数值
# 此值为数字, 单位为秒
DELAY = 0.1

# 是否自动黏贴生成的图片(如果为否则保留图片在剪贴板, 可以手动黏贴)
# 此值为布尔值, True 或 False
AUTO_PASTE_IMAGE = True

# 生成图片后是否自动发送(模拟回车键输入), 只有开启自动黏贴才生效
# 此值为布尔值, True 或 False
AUTO_SEND_IMAGE = True


def copy_png_bytes_to_clipboard(png_bytes: bytes):
    """将 PNG 字节数据复制到剪贴板（跨平台）"""
    try:
        # 在 macOS 上需要使用 osascript 才能正确复制图片
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(png_bytes)
            tmp_path = tmp.name

        # 使用 osascript 复制图片到剪贴板
        cmd = f"""osascript -e 'set the clipboard to (read (POSIX file "{tmp_path}") as «class PNGf»)'"""
        result = subprocess.run(cmd, shell=True, capture_output=True)

        # 清理临时文件
        os.unlink(tmp_path)

        if result.returncode != 0:
            print(f"复制图片到剪贴板失败: {result.stderr.decode()}")
    except Exception as e:
        print(f"复制图片到剪贴板失败: {e}")


def cut_all_and_get_text() -> str:
    """
    模拟 Ctrl+A / Ctrl+X 剪切全部文本，并返回剪切得到的内容。
    跨平台: 在macOS上使用Cmd键代替Ctrl键。
    delay: 每步之间的延时（秒），默认0.1秒。
    """

    # 清空剪贴板，防止读到旧数据
    pyperclip.copy("")

    # 发送 组合键
    kbd_controller.press(Key.ctrl if PLATFORM != 'darwin' else Key.cmd)
    kbd_controller.press('a')
    kbd_controller.release('a')
    kbd_controller.press('x')
    kbd_controller.release('x')
    kbd_controller.release(Key.ctrl if PLATFORM != 'darwin' else Key.cmd)
    time.sleep(DELAY)

    # 获取剪切后的内容
    new_clip = pyperclip.paste()

    return new_clip


def try_get_image() -> Image.Image | None:
    """
    尝试从剪贴板获取图像，如果没有图像则返回 None。
    跨平台支持。
    """
    try:
        # 使用 pyclip 获取剪贴板数据（二进制）
        data = pyclip.paste()

        # 如果是字节类型，尝试解析为图片
        if isinstance(data, bytes) and len(data) > 0:
            # 检查是否是文本数据（通常文本数据较短且可解码）
            try:
                # 尝试解码为文本，如果成功说明不是图片
                text = data.decode('utf-8')
                # 如果解码成功且内容看起来像文本，则不是图片
                if len(text) < 10000:  # 图片数据通常很大
                    return None
            except (UnicodeDecodeError, AttributeError):
                # 解码失败，可能是图片数据
                pass

            # 尝试将字节数据转换为图片
            try:
                image = Image.open(io.BytesIO(data))
                # 验证图片是否有效
                image.load()
                return image
            except Exception as e:
                # 不是有效的图片格式
                return None

    except Exception as e:
        print(f"无法从剪贴板获取图像: {e}")
    return None


def Start():
    print("Start generate...")

    character_name = get_current_character()
    address = os.path.join(magic_cut_folder, get_random_value() + ".jpg")
    BASEIMAGE_FILE = address
    print(character_name, str(1 + (value_1 // 16)), "背景", str(value_1 % 16))

    # 文本框左上角坐标 (x, y), 同时适用于图片框
    # 此值为一个二元组, 例如 (100, 150), 单位像素, 图片的左上角记为 (0, 0)
    TEXT_BOX_TOPLEFT = (mahoshojo_postion[0], mahoshojo_postion[1])
    # 文本框右下角坐标 (x, y), 同时适用于图片框
    # 此值为一个二元组, 例如 (100, 150), 单位像素, 图片的左上角记为 (0, 0)
    IMAGE_BOX_BOTTOMRIGHT = (mahoshojo_over[0], mahoshojo_over[1])
    text = cut_all_and_get_text()
    image = try_get_image()

    if text == "" and image is None:
        print("no text or image")
        return

    png_bytes = None

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
                keep_alpha=True,  # 使用内容图 alpha 作为蒙版
                role_name=character_name,  # 传递角色名称
                text_configs_dict=text_configs_dict,  # 传递文字配置字典
            )
        except Exception as e:
            print("Generate image failed:", e)
            return

    elif text != "":
        print("Get text: " + text)

        try:
            png_bytes = draw_text_auto(
                image_source=BASEIMAGE_FILE,
                image_overlay=None,
                top_left=TEXT_BOX_TOPLEFT,
                bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                text=text,
                align="left",
                valign='top',
                color=(255, 255, 255),
                max_font_height=145,  # 例如限制最大字号高度为 145 像素
                font_path=get_current_font(),
                role_name=character_name,  # 传递角色名称
                text_configs_dict=text_configs_dict,  # 传递文字配置字典
            )

        except Exception as e:
            print("Generate image failed:", e)
            return

    if png_bytes is None:
        print("Generate image failed!")
        return

    copy_png_bytes_to_clipboard(png_bytes)

    if AUTO_PASTE_IMAGE:
        kbd_controller.press(Key.ctrl if PLATFORM != 'darwin' else Key.cmd)
        kbd_controller.press('v')
        kbd_controller.release('v')
        kbd_controller.release(Key.ctrl if PLATFORM != 'darwin' else Key.cmd)

        time.sleep(0.3)

        if AUTO_SEND_IMAGE:
            kbd_controller.press(Key.enter)
            kbd_controller.release(Key.enter)


# 定义全局热键映射
hotkey_bindings = {
    # 角色切换快捷键 Ctrl+1 到 Ctrl+9
    '<ctrl>+1': lambda: switch_character(1),
    '<ctrl>+2': lambda: switch_character(2),
    '<ctrl>+3': lambda: switch_character(3),
    '<ctrl>+4': lambda: switch_character(4),
    '<ctrl>+5': lambda: switch_character(5),
    '<ctrl>+6': lambda: switch_character(6),
    '<ctrl>+7': lambda: switch_character(7),
    '<ctrl>+8': lambda: switch_character(8),
    '<ctrl>+9': lambda: switch_character(9),

    # 角色10-14使用特殊快捷键
    '<ctrl>+q': lambda: switch_character(10),
    '<ctrl>+e': lambda: switch_character(11),
    '<ctrl>+r': lambda: switch_character(12),
    '<ctrl>+t': lambda: switch_character(13),
    '<ctrl>+y': lambda: switch_character(0),

    # 显示当前角色
    '<ctrl>+0': show_current_character,

    # 表情切换 Alt+1-9
    '<alt>+1': lambda: get_expression(1),
    '<alt>+2': lambda: get_expression(2),
    '<alt>+3': lambda: get_expression(3),
    '<alt>+4': lambda: get_expression(4),
    '<alt>+5': lambda: get_expression(5),
    '<alt>+6': lambda: get_expression(6),
    '<alt>+7': lambda: get_expression(7),
    '<alt>+8': lambda: get_expression(8),
    '<alt>+9': lambda: get_expression(9),

    # 生成图片
    '<enter>': Start,

    # 清除图片
    '<ctrl>+<tab>': lambda: delate(magic_cut_folder),
}

# 创建全局热键监听器
listener = GlobalHotKeys(hotkey_bindings)
listener.start()

print("快捷键监听已启动，按 Esc 退出程序")

# 保持程序运行，监听 Esc 键 (或 Ctrl+C) 退出
try:
    with keyboard.Listener(on_press=lambda key: key != Key.esc) as esc_listener:
        esc_listener.join()
except KeyboardInterrupt:
    pass
finally:
    listener.stop()
    print("\n程序已退出")
