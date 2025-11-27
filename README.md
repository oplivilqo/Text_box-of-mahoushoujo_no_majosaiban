## 在原版基础上增加了以下功能
1. 预合成功能的开关（因为我觉得有点占空间）
2. 随机人物差分和背景的开关
3. 图片预览（会预览下一个发送的图片的样子，即使是随机生成背景和人物）

## 程序界面
<img width="501" height="704" alt="2025-11-27 23-50-28" src="https://github.com/user-attachments/assets/cd68754d-3c04-4649-8483-997fec928d2b" />

## 使用须知
1. 目前还有很多bug，我还在修
2. 代码是deepseek写的，补药喷我


# 🎭魔法少女的魔女裁判 文本框生成器

一个基于Python的自动化表情包生成工具，能够快速生成带有自定义文本的魔法少女的魔女裁判文本框图片。[灵感来源与代码参考](https://github.com/MarkCup-Official/Anan-s-Sketchbook-Chat-Box)

## 预览
<img width="1200" height="390" alt="5f10f4239bc8a82812e505fd0c4f5567" src="https://github.com/user-attachments/assets/6fb46a8d-4fc4-4d10-80a0-ed21fbb428bf" />

<img width="1200" height="390" alt="96038673678af657e937d20617322e81" src="https://github.com/user-attachments/assets/847c331e-9274-4b60-9b42-af0a80265391" />


一个基于Python的自动化表情包生成工具，能够快速生成带有自定义文本的魔法少女的魔女裁判文本框图片。[灵感来源与代码参考](https://github.com/MarkCup-Official/Anan-s-Sketchbook-Chat-Box)

<div align="left">

## 修改说明

1.修复了原版生成函数阻塞快捷键识别的bug

2.添加了窗口白名单功能，避免在不需要使用脚本的窗口触发快捷键

3.修复了输出图片时角色名丢失的bug

4.支持系统通用的emoji（TIM由于会自动将输入的emoji变成图片，故暂不支持，QQ未测试）

5.增加了方便的build脚本，生成方式：pyinstaller build_onefile.spec 不知道为啥没办法包含pilemoji库，导致无法生成emoji，建议还是运行py文件

## 功能特色

- 🎨 多角色支持 - 内置14个角色，每个角色多个表情差分，支持自定义角色导入
- ⚡ 终端用户界面 - 使用Textual实现美观的用户界面
- 🖼️ 智能合成 - 自动合成背景与角色图片
- 📝 文本嵌入 - 自动在表情图片上添加文本
- 🎯 随机算法 - 智能避免重复表情

## 使用方法

### 核心功能

1. 切换角色 - 使用UI选择目标角色和表情
2. 输入文本 - 在聊天框或文本编辑器中输入想要添加的文本
3. 生成图片 - 按下 `Ctrl+E` 键自动生成并发送
4. 清理缓存 - 一键清理生成的临时图片

<img width="1203" height="756" alt="image" src="https://github.com/user-attachments/assets/edc38524-f2fd-4c18-8a8d-59f0a0a839bb" />

> ^^^ 提示：底部的按钮可以按 XD

<img width="1203" height="756" alt="image" src="https://github.com/user-attachments/assets/5d1219c4-582f-4573-a605-065d6abc5337" />

> ^^^ 还有进度条！不用干等了 www

### 使用提醒

由于制作时采取了合成图片的思路，第一次切换角色后需要等待读条，无法立即使用

### 添加自定义角色
***
#### 第1步
请下载需要的角色图片，放置于`<根目录>/assets/chara/<角色名>`文件夹中，
并统一命名格式为`<角色名> (<差分编号>)`，如图：
<img width="230" height="308" alt="image" src="https://github.com/user-attachments/assets/892b6c8e-b857-482b-94be-07ad240f2a3b" />
> 注意角色名与编号之间的空格

#### 第2步
修改**2个**配置文件，位于`<根目录>/config`文件夹：
1. `chara_meta.yml`: 包含角色元数据，在末尾添加：
```yaml
warden:  # 填写角色名（与你的文件夹名相同）
  full_name: 典狱长  # 填写角色全名（仅用于可读性显示）
  emotion_count: 1   # 填写差分数量
  font: font3.ttf    # 填写使用的字体
```
2. `text_configs.yml`: 包含角色名称的显示方法，在末尾添加：
```yaml
warden:
  - text: 典 # 文字内容
    position: [ 759, 63 ]  # 绝对坐标
    font_color: [ 195, 209, 231 ]  # 颜色RGB值
    font_size: 196  # 文字大小
  - text: 狱 # 下面以此类推
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
由于制作时采取了合成图片的思路，第一次切换角色后需要等待合成，无法立即使用

另外，若要使用角色，请下载对应角色文件夹并放到main.py文件所在目录中

## 更新日志（学长说最好写个这东西，虽然没写过但是先养成习惯？）

### v1.1.5

- 增添了自主切换表情功能
- 将特殊字体改为红色


### 许可证

本项目基于MIT协议传播，仅供个人学习交流使用，不拥有相关素材的版权。进行分发时应注意不违反素材版权与官方二次创造协定。

## 结语

受B站上MarkCup做的夏目安安传话筒启发，以夏目安安传话筒为源代码编写了这样一个文本框脚本。
由于本人是初学者，第一次尝试写这种代码，有许多地方尚有改进的余地，望多多包含。

更新日志怎么写啊

<div align="right">
  
### 以上. 柊回文————2025.11.15










