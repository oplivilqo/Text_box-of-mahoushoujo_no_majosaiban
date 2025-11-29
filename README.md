# 🎭魔法少女的魔女审判 文本框生成器 (JavaScript实现)

一个表情包生成工具，能够快速生成带有自定义文本的魔法少女的魔女审判文本框图片。

此分支在保留[主分支](https://github.com/oplivilqo/manosaba_text_box)Python脚本的同时添加了使用浏览器JavaScript实现、无需Python环境的版本，可能更适合偶尔生成图片的用户。Python脚本使用方法请见主分支说明。

JavaScript版与Python版共用同一组素材与配置文件。

![界面截图](https://github.com/user-attachments/assets/38d0e142-8707-4f43-b1a8-1bb0bcdbe848)

## 使用方法

直接下载整个仓库然后本地使用浏览器打开`index.html`即可使用。无需部署到Web服务器，不过首次本地访问需要手动上传`config/chara_meta.yml`和`config/text_configs.yml`两个配置文件，对于手机端用户可能还是部署到服务器访问更方便一些吧……

~~都有GUI了应该不用再多说什么了吧……~~

### 添加自定义角色（同主分支Python版本）
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

## 已测试环境

已在 `Windows`、`MacOS`、`Android` 系统的 `Chromium` 内核浏览器上测试过，功能正常。理论上来说应该现代浏览器都能支持。某种程度上也是跨平台了？（雾）

## 版权相关

仅供个人学习交流使用，各类素材均归属于相关版权方。

背景、立绘等图片素材 © Re,AER LLC./Acacia

