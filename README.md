Textual TUI 分支

# 🎭魔法少女的魔女裁判 文本框生成器

一个基于Python的自动化表情包生成工具，能够快速生成带有自定义文本的魔法少女的魔女裁判文本框图片。[灵感来源与代码参考](https://github.com/MarkCup-Official/Anan-s-Sketchbook-Chat-Box)

## 功能预览：
<img width="600" height="195" alt="5f10f4239bc8a82812e505fd0c4f5567" src="https://github.com/user-attachments/assets/6fb46a8d-4fc4-4d10-80a0-ed21fbb428bf" />

<img width="600" height="195" alt="96038673678af657e937d20617322e81" src="https://github.com/user-attachments/assets/847c331e-9274-4b60-9b42-af0a80265391" />

## 分支说明：
本分支由Kwicxy基于oplivilqo的项目二次开发，基于textual实现了终端用户界面以及其它实用功能。

**主要更新功能：**
1. 不再使用磁盘缓存，改为实时缓存在内存中，缓存大小可调，默认为100MB (约3个角色)
2. 添加了随机人物差分的开关
3. 更快速合理的自定义角色功能
4. 添加了快捷键自定义功能
5. 添加了目标窗口白名单功能
6. 添加了uv安装方式，推荐使用uv安装依赖，速度更快
7. 优化了程序结构与代码风格
8. 修复了一些已知bug
9. 自定义角色图片会自动缩放以适应文本框

## 界面预览：

<img width="1203" height="756" alt="image" src="https://github.com/user-attachments/assets/5d1219c4-582f-4573-a605-065d6abc5337" />

> ^^^ 提示：底部的按钮可以按 XD
> ^^^ 还有进度条！不用干等了 www

## 安装与使用：

### 环境要求：

- **Python** 3.11 或更高版本
- **pip** 或 **uv** 包管理器（二选一）
- **Git** 用于克隆仓库

在安装之前，先克隆仓库：
```bash
# 克隆仓库
git clone https://github.com/oplivilqo/manosaba_text_box.git
cd manosaba_text_box
# 切换到 TUI 分支
git checkout refresh
```

### 方案一：使用 uv 安装（推荐）

#### 1. 安装 uv

如果还没有安装 uv，请先安装：
```bash
curl -LsSf https://astral. sh/uv/install.sh | sh
```

或访问 [uv 官网](https://github.com/astral-sh/uv) 查看其他安装方式。

#### 2. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
# 根据你的系统在下面两条命令二选一
source . venv/bin/activate  # Linux/macOS
. venv\Scripts\activate  # Windows

# 安装依赖
uv sync
```

---

### 方案二：使用 pip 安装（兼容性）

#### 1. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# 根据你的系统在下面两条命令二选一
source . venv/bin/activate  # Linux/macOS
. venv\Scripts\activate  # Windows
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

---

### ⚡ 启动程序

安装完依赖后，选择以下方式之一启动程序：

**TUI 界面版**

```bash
python tui.py
```

**命令行版**

```bash
python main. py
```

---
### 添加自定义角色
#### 方法一：手动添加
##### 第1步
在`<根目录>/assets/chara/`文件夹中创建一个以角色名命名的文件夹，
如`warden`，然后将角色的所有表情图片放置于该文件夹中，
并统一命名格式为`<角色名> (<差分编号>)`，如图：

<img width="230" height="308" alt="image" src="https://github.com/user-attachments/assets/892b6c8e-b857-482b-94be-07ad240f2a3b" />

> 注意角色名与编号之间的空格

##### 第2步
在角色文件夹中新建配置文件`meta.yml`，格式如下：
```yaml
# 新角色信息，依次为全名、使用的字体
full_name: 典狱长
font: font3.ttf
# 新角色的文字配置（对话框上方角色的名字显示）
# 依次为文字内容、位置（x, y）、字体颜色（R, G, B）、字体大小
text_config:
  - text: 典
    position: [ 759, 63 ]
    font_color: [ 195, 209, 231 ]
    font_size: 196
  - text: 狱
    position: [ 948, 175 ]
    font_color: [ 255, 255, 255 ]
    font_size: 92
  - text: 长
    position: [ 1053, 117 ]
    font_color: [ 255, 255, 255 ]
    font_size: 147
  - text: ""
    position: [ 0, 0 ]
    font_color: [ 255, 255, 255 ]
    font_size: 1
```

### 删除自定义角色
直接删除`<根目录>/assets/chara/`中对应角色的文件夹即可

---

### 🔧 常见问题

**Q: 我应该选择 uv 还是 pip？**

A: 推荐使用 uv，因为：
- 安装速度快 10 倍
- 依赖解析更准确
- 内存占用更低
- 但如果你已经熟悉 pip，两者都可以用

**Q: 按快捷键没有反应？**

A: 请确保目标窗口在白名单中（在 TUI 界面中配置）

**Q: macOS 上无法运行？**

A: 请检查 `设置 > 隐私和安全 > 辅助功能 / 输入监控` 启用 `Python.app`

