# 未完成 · 遗忘

一款文艺风格的桌面笔记软件，以泛黄纸张为画布，记录那些未完成的事与终将遗忘的人。

基于 PyQt5 开发，无边框磨砂 UI、纯画布模式、动态光影氛围，支持 AI 批注、归档收藏与导出。

## 功能特性

- **画布笔记**：无边框纸张画布，自由书写，支持多页切换
- **氛围模式**：动态光影、磨砂 UI、多种纸张色调，营造沉浸书写氛围
- **深色模式**：一键切换深色主题，夜间书写不刺眼
- **纯模式**：隐藏工具栏与状态栏，进入纯粹书写状态
- **AI 对话**：接入豆包大模型，AI批注
- **归档收藏**：重要页面归档保存，归档网格浏览
- **导出功能**：支持将笔记导出为文本或图片
- **字体管理**：内置文艺字体，支持自定义字体
- **快捷键**：丰富的键盘快捷键，高效操作
- **本地存储**：json 文件，所有数据仅存于本机

## 技术栈

| 模块 | 技术选型 |
|------|----------|
| 开发语言 | Python 3 |
| UI 框架 | PyQt5 |
| 图像处理 | Pillow |
| 本地数据库 | json文件 |
| AI 模型 | 豆包（火山方舟 ARK） |
| 打包工具 | PyInstaller |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行

```bash
python main.py
```

或双击 `run.bat` 启动。

### 3. 配置 AI（可选）

在软件中打开 AI 对话框，填入豆包 API Key 即可使用 AI 对话与续写功能。
API Key 本地加密存储，不上传任何服务器。

## 打包 EXE

使用 PyInstaller 打包：

```bash
# 单文件版
pyinstaller 未完成遗忘_onefile.spec

# 目录版
pyinstaller 未完成遗忘.spec
```

打包产物在 `dist/` 目录下。

## 项目结构

```
.
├── main.py                  # 主入口
├── requirements.txt         # 依赖
├── run.bat                  # Windows 启动脚本
├── 1.ico                    # 应用图标
├── 未完成遗忘.spec           # PyInstaller 配置（目录版）
├── 未完成遗忘_onefile.spec   # PyInstaller 配置（单文件版）
├── assets/
│   ├── backgrounds/         # 纸张背景图
│   ├── fonts/               # 字体文件
│   └── sounds/              # 音效（预留）
├── data/                    # 运行时数据（数据库自动生成）
├── utils/
│   ├── ai_client.py         # 豆包 AI 客户端
│   ├── constants.py         # 常量、文案、主题色
│   ├── db.py                # json 文件封装
│   └── helpers.py           # 工具函数
└── widgets/
    ├── canvas.py            # 画布组件
    ├── toolbar.py           # 工具栏
    ├── statusbar.py         # 状态栏
    ├── archive.py           # 归档侧边栏
    ├── archive_grid.py      # 归档网格
    ├── archive_trigger.py   # 归档触发器
    ├── api_dialog.py        # AI 配置对话框
    ├── export_dialog.py     # 导出对话框
    ├── font_manager_dialog.py # 字体管理
    ├── guide.py             # 新手引导
    ├── menus.py             # 菜单与快捷键说明
    ├── rounded_dialogs.py   # 圆角对话框
    └── round_helper.py      # 圆角绘制辅助
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+N | 新建页面 |
| Ctrl+E | 导出 |
| Ctrl+Back | 返回 |
| Ctrl+Shift+A | 归档 |
| F11 | 全屏 |
| Ctrl+P | 纯模式 |
| Ctrl+L | 氛围模式 |
| Ctrl+D | 深色模式 |

## 数据安全

所有笔记数据存储在本地 `data/` 目录下的 json 文件中，不会上传到任何服务器。
AI 功能仅在你主动发起对话时将当前内容发送至豆包 API。

## 免责声明

本软件为个人学习与创作项目，AI 生成内容仅供参考，请自行甄别与判断。


## 赞助

如果这个项目对你有帮助，欢迎赞助支持，感谢你的每一份鼓励：

[![爱发电](https://img.shields.io/badge/赞助-爱发电-946ce6)](https://www.ifdian.net/a/yanziqin5)

[去爱发电赞助我](https://www.ifdian.net/a/yanziqin5)

## License

本项目基于 [MIT License](LICENSE) 开源。
