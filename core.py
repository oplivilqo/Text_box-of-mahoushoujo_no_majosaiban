# -*- coding: utf-8 -*-
#读取资源，合成图片，返回PNGbytes，预处理
import sys
import random
import os
import getpass
import logging
import time
from PIL import Image
from text_fit_draw import draw_text_auto,draw_name
from image_fit_paste import paste_image_auto

logger = logging.getLogger(__name__)

# 图片缓存字典 - 存储已加载的图片
_image_cache = {}
_cache_enabled = True

#全局变量区
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
    {"text":"雪","position":(1053,117),"font_color":(255, 255, 255),"font_size":147} ,   
    {"text":"","position":(0,0),"font_color":(255, 255, 255),"font_size":1}
        ]
}

#文本框范围
mahoshojo_postion = [728,355] #文本范围起始位置
mahoshojo_over = [2339,800]   #文本范围右下角位置
#变量区结束




#函数区
#获取绝对路径
def get_resource_path(related_path):
    try:
        base_path = sys._MEIPASS #pyinstaller创建的临时目录
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__)) #未打包时的目录
    return os.path.join(base_path, related_path)

#获取用户魔裁文件夹路径，若不存在则创建
def get_magic_cut_folder():
    # 获取当前用户名
    username = getpass.getuser()
    # 构建用户文档路径
    if os.name == 'nt':  # Windows系统
        user_documents = os.path.join('C:\\Users', username, 'Documents')
    else:  # 其他系统
        user_documents = os.path.expanduser('~/Documents')
    # 构建"魔裁"文件夹路径
    magic_cut_folder = os.path.join(user_documents, '魔裁')
    # 创建"魔裁"文件夹（如果不存在）
    os.makedirs(magic_cut_folder, exist_ok=True)
    return magic_cut_folder

#启用/禁用缓存（等待后续加到gui里）
def set_cache_enabled(enabled: bool):
    global _cache_enabled
    _cache_enabled = enabled
    if not enabled:
        clear_image_cache()




#清空图片缓存
def clear_image_cache():
    global _image_cache
    _image_cache.clear()
    logger.info("图片缓存已清空")

#从缓存或磁盘加载图片
def load_image_cached(image_path: str) -> Image.Image:
    if not _cache_enabled:
        return Image.open(image_path).convert("RGBA")
    
    if image_path not in _image_cache:
        try:
            img = Image.open(image_path).convert("RGBA")
            _image_cache[image_path] = img
            logger.debug(f"图片已缓存: {os.path.basename(image_path)}")
        except Exception as e:
            logger.exception(f"加载图片失败 {image_path}: {e}")
            raise
    
    # 返回副本
    return _image_cache[image_path].copy()

#预处理资源文件并保存到文件夹（新增了回传功能~）
def prepare_resources(callback=None):
    #回传~
    def _cb(msg):
        try:
            if callback:
                callback(msg)
        except Exception:
            logger.exception('回传错误')
    magic_cut_folder = get_magic_cut_folder()

    for character_name in mahoshojo.keys():
        _cb(f"正在预处理：{character_name}")
        logger.info("正在预处理：%s", character_name)
        emotion_count = mahoshojo[character_name]["emotion_count"]
        existing_count = sum(1 for entry in os.scandir(magic_cut_folder) if entry.is_file() and entry.name.startswith(character_name))
        if existing_count == 16 * emotion_count:
            _cb("已存在，跳过")
            logger.info("已存在，跳过 %s", character_name)
            continue
        else:
            for entry in os.scandir(magic_cut_folder):
                if entry.is_file() and entry.name.startswith(character_name):
                    try:
                        os.remove(entry.path)
                        _cb(f"删除旧文件：{entry.name}")
                        logger.info("删除旧文件：%s", entry.name)
                    except Exception:
                        logger.exception("删除文件失败: %s", entry.path)
        for i in range(16):
            for j in range(emotion_count):
                #更新为新的目录结构
                background_path = get_resource_path(os.path.join('assets', 'background', f"c{i+1}.png"))
                overlay_path = get_resource_path(os.path.join('assets', 'chara', character_name, f"{character_name} ({j+1}).png"))

                try:
                    background = Image.open(background_path).convert("RGBA")
                except Exception as e:
                    _cb(f"无法打开背景图像文件 {background_path} ：{e}")
                    logger.exception("无法打开背景图像文件 %s : %s", background_path, e)
                    continue

                try:
                    overlay = Image.open(overlay_path).convert("RGBA")
                except Exception as e:
                    _cb(f"无法打开叠加图像文件 {overlay_path} ：{e}")
                    logger.exception("无法打开叠加图像文件 %s : %s", overlay_path, e)
                    continue

                img_num = j * 16 + i + 1
                result = background.copy()
                result.paste(overlay, (0, 134), overlay)

                #画名字
                result=draw_name(result,text_configs_dict,character_name)

                save_path = os.path.join(magic_cut_folder, f"{character_name} ({img_num}).jpg")
                try:
                    result.convert("RGB").save(save_path)
                    _cb(f"已生成：{os.path.basename(save_path)}")
                    logger.info("已生成：%s", save_path)
                except Exception:
                    logger.exception("保存文件失败: %s", save_path)
        _cb(f"预处理完毕：{character_name}")
        logger.info("预处理完毕：%s", character_name)

    #预热缓存
    _cb("正在预热图片缓存...")
    logger.info("开始预热图片缓存")
    preheat_cache()
    _cb("缓存预热完成")
    logger.info("缓存预热完成")

def preheat_cache():
    if not _cache_enabled:
        return
    
    magic_cut_folder = get_magic_cut_folder()
    #只预加载每个角色的前几张图片，避免占用过多内存
    for character_name in mahoshojo.keys():
        emotion_count = mahoshojo[character_name]["emotion_count"]
        #预加载每个表情的第一张
        for j in range(min(emotion_count, 3)):  #限制预加载数量
            img_num = j * 16 + 1
            image_path = os.path.join(magic_cut_folder, f"{character_name} ({img_num}).jpg")
            if os.path.exists(image_path):
                try:
                    load_image_cached(image_path)
                except Exception:
                    logger.exception(f"预热缓存失败: {image_path}")

#不重复的随机表情生成
def get_random_expression(character_name,last_value=-1,expression=-1):
    if character_name not in mahoshojo:
        raise ValueError(f"角色名称 '{character_name}' 无效。")
    
    if expression != -1:
        if expression < 1 or expression > mahoshojo[character_name]["emotion_count"]:
            expression = (expression - 1) % mahoshojo[character_name]["emotion_count"] + 1
            logger.info(f"表情值超出范围，已调整为有效值：{expression}")
        bg=random.randint(1,16)
        img_num = (expression - 1) * 16 + bg
        return os.path.join(get_magic_cut_folder(), f"{character_name} ({img_num}).jpg"),expression

    max_attempts = 10  # 最大尝试次数
    attempts = 0
    while (expression==-1 or expression==last_value) and attempts < max_attempts:
        expression=random.randint(1, mahoshojo[character_name]["emotion_count"])
        attempts += 1
    if attempts >= max_attempts:
        logger.warning("达到最大尝试次数，返回随机表情")
        expression = random.randint(1, mahoshojo[character_name]["emotion_count"])
    return os.path.join(get_magic_cut_folder(), f"{character_name} ({(expression - 1) * 16 + random.randint(1,16)}).jpg"),expression

#图片生成
def generate_image(text,content_image,role_name,font_path='font3.ttf',last_value=-1,expression=-1):
    if not text and content_image is None:
        logger.warning("没有文本/图像")
        return None, expression
    png_bytes=None
    # 记录开始时间并在返回前记录耗时到日志
    start_ts = time.perf_counter()
    try:
        address, expression = get_random_expression(role_name,last_value,expression)

        # 文本框左上角坐标 (x, y), 同时适用于图片框
        TEXT_BOX_TOPLEFT= (mahoshojo_postion[0], mahoshojo_postion[1])
        # 文本框右下角坐标 (x, y), 同时适用于图片框
        IMAGE_BOX_BOTTOMRIGHT= (mahoshojo_over[0], mahoshojo_over[1])
        
        #处理图片
        if content_image is not None:
            try:
                logger.info("检测到图片")
                # 使用缓存加载
                base_image = load_image_cached(address)
                png_bytes = paste_image_auto(
                    image_source=base_image,  # 直接传入Image对象
                    image_overlay=None,
                    top_left=TEXT_BOX_TOPLEFT,
                    bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                    content_image=content_image,
                    align="center",
                    valign="middle",
                    padding=12,
                    allow_upscale=True, 
                    keep_alpha=True,      # 使用内容图 alpha 作为蒙版 
                    role_name=role_name,  # 传递角色名称
                    text_configs_dict=text_configs_dict,  # 传递文字配置字典
                )
            except Exception as e:
                logger.error("图片处理出错：%s", e)
                return None, expression
        elif text:
            try:
                logger.info('检测到文本：%s', text)
                # 使用缓存加载
                base_image = load_image_cached(address)
                png_bytes = draw_text_auto(
                    image_source=base_image,  # 直接传入Image对象
                    image_overlay=None,
                    top_left=TEXT_BOX_TOPLEFT,
                    bottom_right=IMAGE_BOX_BOTTOMRIGHT,
                    text=text,
                    align="left",
                    valign='top' ,
                    color=(255, 255, 255), 
                    max_font_height=145,        # 例如限制最大字号高度为 145 像素
                    font_path=font_path,
                    role_name=role_name,  # 传递角色名称
                    text_configs_dict=text_configs_dict,  # 传递文字配置字典
                )
            except Exception as e:
                logger.error("文本处理出错：%s", e)
                return None, expression

        return png_bytes, expression
    finally:
        end_ts = time.perf_counter()
        duration_ms = (end_ts - start_ts) * 1000.0
        try:
            logger.info("生成信息: role=%s expression=%s mode=%s duration=%.1fms", role_name, expression, 'image' if content_image is not None else 'text', duration_ms)
        except Exception:
            # 保底，不影响主流程
            logger.info("生成耗时: %.1fms", duration_ms)