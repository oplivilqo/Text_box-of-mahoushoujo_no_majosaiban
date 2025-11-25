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

mahoshojo_postion = [728,355] #文本范围起始位置
mahoshojo_over = [2339,800]   #文本范围右下角位置










import random
import time
import keyboard
import pyperclip
import io
from PIL import Image
import win32clipboard
import os
import yaml

from text_fit_draw import draw_text_auto
from image_fit_paste import paste_image_auto

i = -1
value_1 = -1
expression = None

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
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "configs.yml")
with open(CONFIG_PATH, 'r', encoding="utf-8") as fp:
    config = yaml.safe_load(fp)

mahoshojo = config["mahoshojo"]
text_configs_dict = config["text_configs"]
character_list = list(mahoshojo.keys())

# 获取当前角色信息
def get_current_character():
    return character_list[current_character_index-1]

def get_current_font():
    # 返回完整的字体文件绝对路径
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), mahoshojo[get_current_character()]["font"])

def get_current_emotion_count():
    return mahoshojo[get_current_character()]["emotion_count"]

def delete(folder_path):
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
            background_path = os.path.join(now_file, 'assets', "background", f"c{i+1}.png")
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
        print("Get text: "+text)

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
                )

        except Exception as e:
            print("Generate image failed:", e)
            return
        
    if png_bytes is None:
        print("Generate image failed!")
        return
    
    copy_png_bytes_to_clipboard(png_bytes)
    
    if AUTO_PASTE_IMAGE:
        keyboard.send(PASTE_HOTKEY)

        time.sleep(0.3)

        if AUTO_SEND_IMAGE:
            keyboard.send(SEND_HOTKEY)

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
keyboard.add_hotkey('ctrl+Tab', lambda: delete(magic_cut_folder))

for i in range(1,10):
    keyboard.add_hotkey(f'alt+{i}', lambda idx=i: get_expression(idx))

# 绑定 Ctrl+Alt+H 作为全局热键
ok=keyboard.add_hotkey(HOTKEY,Start, suppress=BLOCK_HOTKEY or HOTKEY==SEND_HOTKEY)

# 绑定Ctrl+0显示当前角色
keyboard.add_hotkey('ctrl+0', show_current_character)

# 保持程序运行
keyboard.wait("Esc")