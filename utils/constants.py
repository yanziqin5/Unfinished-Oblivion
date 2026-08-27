"""
《未完成·遗忘》全局常量 —— 氛围升级版。
"""
import os
import sys
import time

# ========== 路径 ==========
# 开发模式：PROJECT_DIR 为源码根目录。
# 打包后（PyInstaller 单文件模式）：__file__ 指向临时只读目录 _MEIPASS，
# 只读资源（assets）可用该路径定位；但用户数据必须持久化到 exe 同目录，
# 否则每次启动都会新建空白库、笔记全部丢失。
if getattr(sys, "frozen", False):
    PROJECT_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "notebook.db")

# ========== 文字生命周期 (秒) —— 需求文档规定 ==========
GAZE_REVIVE_ALPHA = 0.95                  # 凝视临时提亮目标透明度（移开立即退回褪色）

# ========== 字体 ==========
SYSTEM_FONT = "Microsoft YaHei"
SERIF_FONT = "Source Han Serif SC"        # 思源宋体（文档规定正文用衬线体，无则降级 SimSun）
SERIF_FONT_FALLBACK = "SimSun"
GUIDE_FONT = "KaiTi"                       # 引导页文字：楷体（Windows 自带，缺失时 Qt 自动回退）
BODY_FONT_SIZE = 12                        # 正文 12pt（更协调的页面比例）
LINE_STEP = 22                             # 正文行高/行距（约字号 1.8 倍，留白呼吸；用于文字重排与光标定位）
REVIVE_HOVER_MIN_ALPHA = 0.25               # 凝视续命的最小透明度阈值：仅当用户自己写的、且已淡到该值以下（快要消失）的字被注视时才续命

# ========== 画布纸张纹理色 ==========
BG_DEFAULT = "#F6F3E9"
BG_YELLOW_1 = "#F6F3E9"
BG_YELLOW_2 = "#F8F5ED"
BG_YELLOW_3 = "#EDE9DD"
BG_YELLOW_4 = "#E8E2D2"

# ========== 昼夜纸色调（真实时钟感知） ==========
# 晨 5:00-8:00 → 微凉青灰暖调（晨光初透）
# 昼 8:00-17:00 → 标准暖黄（阳光铺满）
# 暮 17:00-20:00 → 琥珀金调（黄昏低斜）
# 夜 20:00-5:00 → 深褐静谧（烛火/灯下）
DAYNIGHT_DAWN_COLOR = "#F0EDE6"           # 晨：冷中带暖
DAYNIGHT_NOON_COLOR = "#F8F4EB"           # 午：标准暖黄
DAYNIGHT_DUSK_COLOR = "#F2E8D8"           # 暮：琥珀金
DAYNIGHT_NIGHT_COLOR = "#EBE4D4"           # 夜：深褐暖

PAPER_BG_MAP = {
    "黄1": "assets/backgrounds/yellow_1.jpg",
    "黄2": "assets/backgrounds/yellow_2.jpg",
    "黄3": "assets/backgrounds/yellow_3.jpg",
    "黄4": "assets/backgrounds/yellow_4.jpg",
}

PAPER_BG_HEX = {
    "黄1": "#F6F3E9",
    "黄2": "#F8F5ED",
    "黄3": "#EDE9DD",
    "黄4": "#E8E2D2",
}

# ========== 写作区约束（文字只能写在中央区域，批注出现在四周留白）==========
WRITING_AREA_MARGIN = 48                 # 四边留白 48px（需求文档规定）

# ========== 色调（需求文档精确色值）==========
TEXT_COLOR = "#5A5548"
HINT_TEXT_COLOR = "#999589"
HINT_TEXT_COLOR_DARK = "#7A7068"
GHOST_TEXT_COLOR = "#C4BEB4"    # 残影文字/空画布淡残影

# 墨水氧化阶段色
INK_FRESH = "#5A5548"          # 鲜墨 0%（与正文墨色一致）
INK_OXIDIZED_1 = "#4A4038"     # 微氧化 20-40%
INK_OXIDIZED_2 = "#7A6238"     # 中度氧化 40-70%（偏黄褐）
INK_OXIDIZED_3 = "#A07C45"     # 深度氧化 70-90%（偏黄褐）
INK_GHOST = "#B59A66"          # 即将消散 90-100%（泛黄）

# ========== 按钮（浅色模式：暖中棕陶底 + 暖米字，比深色模式更亮一档，在米纸上明显但不刺眼）==========
BUTTON_BG = "#8C7B65"              # 暖中棕底色（深于纸面 #F6F3E9、浅于深色 #3C362C）
BUTTON_HOVER_BG = "#7D6D58"        # 悬停略深
BUTTON_PRESSED_BG = "#6E5F4C"      # 按下更实
BUTTON_TEXT = "#F5F0E8"            # 暖白字（中棕底上清晰可读）
CONTROL_RADIUS = 12                # 控件统一大圆角（浅色/深色共用）

# ========== 全局动画时长 (ms) —— 需求文档精确值 ==========
DURATION_BREATHING_CYCLE = 8000           # 文字呼吸完整周期（放慢，静谧）
DURATION_SIDEBAR_SLIDE = 700              # 侧边栏展开/收起（放慢，温柔）
SIDEBAR_WIDTH = 320                       # 侧边栏展开后的宽度
DURATION_TOAST_FADE = 500                 # Toast 淡入段（文档规定 500ms）
DURATION_TOAST_VISIBLE = 1500             # Toast 可见停留（文档规定 1500ms）
DURATION_TOAST_FADE_OUT = 800             # Toast 淡出段（文档规定 800ms）
DURATION_GUIDE_FADE = 900                 # 引导页淡出（放慢，避免一闪而过）
DURATION_COMMENT_STROKE = 2000            # AI 批注逐笔浮现总时长（拉长）
DURATION_DISSOLVE_PARTICLE = 6000         # 文字消散粒子动画总时长（拉长，缓慢流逝）
DURATION_LIGHT_SWEEP = 52000             # 窗边暖柔光移动周期（再放慢，光影更缓）
DURATION_TEXTURE_DRIFT = 40000           # 纸纤维纹理微动周期（再放慢）
DURATION_DUST_DRIFT = 14000               # 尘埃粒子漂移周期（放慢）

# ========== 文字生命周期 (秒) ==========
LIFE_BASE_SEC = 21600                     # 基础自然寿命 6 小时；放任不管约半天左右开始大面积淡出消散
LIFE_MAX_SEC = 432000                     # 全局硬封顶 120 小时（5天）：记忆最多被挽留 5 天，到时限终归消散
LIFE_DECAY_WARN_RATIO = 0.25             # 衰退预警阈值：寿命消耗 ≥75%（alpha ≤0.25）时触发第一段预警
LIFE_END_WARN_RATIO = 0.10               # 临终预警阈值：寿命消耗 ≥90%（alpha ≤0.10）时触发第二段预警
LIFE_DYING_RATIO = 0.02                  # 弥留阶段：剩余寿命 ≤ 2%，进入缓慢消融
LIFE_DYING_DURATION_SEC = 60             # 弥留阶段持续时间（1分钟），避免死后残影长期漂浮显混乱

# ========== 残影效果 ==========
AFTERGLOW_DURATION_SEC = 60              # 文字完全消散后，残影保留时间（1分钟）
AFTERGLOW_MAX_ALPHA = 0.08               # 残影最大透明度

# ========== 悬停续命动画 ==========
GAZE_REVIVE_SPEED = 0.02                 # 悬停/续命时透明度提升速度（每帧增加量，放慢以更柔和）
FADE_DECAY_SPEED = 0.015                 # 离开后恢复到基准透明度的速度（每帧衰减量）
REVIVE_FLASH_DURATION = 3.5              # 续命回润脉冲总时长（秒，sin 包络渐入→峰→渐出，更柔和）

# 续命梯度严格递减（记忆最多被人为挽留 5 天，到时限依旧归于消散）
# 第1次 +172800s(48h), 第2次 +86400s(24h), 第3次 +43200s(12h), 第4次 +14400s(4h), 第5次 +7200s(2h)
# 5 次累加 90h，叠加基础寿命后单字理论最长 ≈ 96h；≥6次仅提亮，不增加寿命、不计数
REVIVE_BONUS_GRADIENT = [172800, 86400, 43200, 14400, 7200]
REVIVE_MAX_COUNT = 5                      # 最多续命5次有效，第6次仅提亮

# ========== 悬停续命 ==========
HOVER_HOLD_MS = 300                      # 悬停触发续命延迟（需求文档规定 ≥300ms）
HOVER_RADIUS_PX = 22                     # 续命判定半径

# ========== 残影 & 尘埃 ==========
GHOST_DUST_COLORS = ["#9C7B3F", "#B59656", "#876C38", "#A88A50"]  # 黄褐半透明尘埃
GHOST_DUST_RADIUS_MIN = 3               # 尘埃柔斑最小半径
GHOST_DUST_RADIUS_MAX = 10              # 尘埃柔斑最大半径
GHOST_MAX_DOTS = 500                     # 消散点位上限
DUST_PARTICLE_COUNT = 15                 # 单字消散拆分粒子数
DUST_PARTICLE_MAX = 80                   # 画布漂浮尘埃上限
DUST_PARTICLE_RADIUS_MIN = 1.0
DUST_PARTICLE_RADIUS_MAX = 2.8
DUST_PARTICLE_BASE_SPEED = 8.0          # 像素/秒，漂浮
DUST_COLORS = ["#B8A88E", "#C4B4A0", "#A89880", "#D0C4B0"]

# ========== 纸纤维纹理参数 ==========
FIBER_LINE_COUNT = 170                   # 纤直线条数
FIBER_COLOR_BASE = "#D8D0C0"
FIBER_ALPHA_MAX = 0.14
FIBER_DRIFT_AMPLITUDE = 1.2             # 微动振幅（像素）

# ========== 纸面细颗粒（纸齿质感）==========
PAPER_GRAIN_OPACITY = 0.55              # 程序化颗粒叠加强度
PAPER_GRAIN_TILE = 320                  # 颗粒贴图分辨率（越大越细腻、生成越慢）

# ========== 黄斑参数 ==========
STAIN_COUNT = 25                         # 随机黄斑数
STAIN_COLORS = ["#E8DCC0", "#DDD0B4", "#E4D8B8", "#EDE0C8"]
STAIN_ALPHA_MAX = 0.12
STAIN_RADIUS_MIN = 8
STAIN_RADIUS_MAX = 35

# ========== 折痕参数 ==========
CREASE_COUNT = 5                         # 淡折痕数量
CREASE_COLOR = "#D0C8B4"
CREASE_ALPHA = 0.09
CREASE_WIDTH = 1.0

# ========== 两段预警线条 ==========
# 衰退预警线（第一段，ratio≥0.75）：极淡虚线，提示"字开始褪色"，给用户较早窗口挽留
# 临终预警线（第二段，ratio≥0.90）：更明显的虚线，提示"再不注意就要消失了"
# 深色模式用暖灰（暗底上清晰）；浅色模式用深褐灰，米色画布上可见。
DECAY_LINE_COLOR = "#C8C2B4"            # 深色模式：衰退预警，略暖
DECAY_LINE_ALPHA = 0.035
DECAY_LINE_COLOR_LIGHT = "#C0AE96"      # 浅色模式：衰退预警（加深以提升米纸对比）
DECAY_LINE_ALPHA_LIGHT = 0.18
WARNING_LINE_COLOR = "#D1CDC0"          # 深色模式：临终预警
WARNING_LINE_ALPHA = 0.07
WARNING_LINE_COLOR_LIGHT = "#9A8A6E"    # 浅色模式：临终预警
WARNING_LINE_ALPHA_LIGHT = 0.32

# ========== 光标颜色 ==========
CURSOR_COLOR = "#5A5548"                # 浅色模式：暖墨色竖笔
CURSOR_COLOR_DARK = "#C8B898"           # 深色模式：淡暖米色竖笔
CURSOR_GLOW_COLOR = "#7A6A58"           # 浅色模式：外层柔光
CURSOR_GLOW_COLOR_DARK = "#D8C8A8"      # 深色模式：外层柔光

# ========== 雾面蒙版颜色 ==========
FROST_BASE = (245, 241, 232)            # 浅色模式：整体磨砂底
FROST_BASE_DARK = (26, 24, 21)          # 深色模式：整体磨砂底
FROST_GRAIN = (232, 228, 219)           # 浅色模式：颗粒噪点底色
FROST_GRAIN_DARK = (42, 40, 37)         # 深色模式：颗粒噪点底色
FROST_LIGHT = (251, 248, 241)           # 浅色模式：顶部窗光晕
FROST_LIGHT_DARK = (35, 32, 26)         # 深色模式：顶部窗光晕

# ========== 临终辉光（回光返照）==========
# 深色模式用暖金光晕（暗底上发光感明显）；浅色模式米色画布会"吃掉"暖金，
# 改用低饱和暖赭/焦土色——靠"比纸面暗的明度对比"保证可见，而非高饱和红铜，
# 避免在高明度米纸上显得像报错高亮般突兀。
TERMINAL_GLOW_DARK = "#E6BE6E"           # 暖琥珀金：深底上更润、不发飘的临终余温
TERMINAL_GLOW_LIGHT = "#BD5E36"           # 焦土赭（比原 #C56A43 更深一档）：米纸上沉得进去、不刺眼的余温

# ========== AI 批注参数（三层渐进解锁：旧主人魂魄苏醒） ==========
COMMENT_MAX_COUNT = 8
PAUSE_DETECTION_MS = 1200              # 用户停止输入 1200ms 发起请求（文档规定）
MIN_CHARS_FOR_COMMENT = 12             # 至少写了这么多字，旧主人才有话说
COMMENT_COOLDOWN_MS = 20000            # 两次批注最小间隔 20 秒
COMMENT_PROB = 0.6                     # 停笔时触发概率（不是每次都说话）
COMMENT_FONT_SIZE = 10
COMMENT_ALPHA_LAYER1 = 0.15             # 最虚层（更淡，下限 0.15）
COMMENT_ALPHA_LAYER2 = 0.25             # 中层
COMMENT_ALPHA_LAYER3 = 0.35             # 最实层（上限 0.35）

# ========== 批注三层解锁体系 ==========
# --- Tier 1：浅层随机解锁 ---
TIER1_UNLOCK_PROB = 0.30               # 每次打开页面 30% 概率新增一条
TOAST_TIER1_UNLOCK = "旧主人似乎又留下了一句话……"

# --- Tier 2：语义关键词解锁 ---
TIER2_KEYWORDS = [
    "孤独", "遗憾", "夜晚", "离别", "等待",
    "想念", "难过", "释怀", "晚风", "回忆", "再见",
]
TOAST_TIER2_UNLOCK = "旧主人似乎也经历过这一刻……"

# --- Tier 3：深层尘封解锁 ---
TIER3_MIN_SENTENCE_CHARS = 15          # 单句连续文字 ≥15 字
TIER3_KEYWORD_REPEAT = 3               # 同一关键词重复 ≥3 次
TIER3_MIN_REVIVES = 3                  # 同一主题对应文字累计续命 ≥3 次
TIER3_MAX_PAGE_TURNS = 3               # 单页最多 3 次翻页动画
TIER3_MAX_PER_PAGE = 2                  # 每页深层埋藏批注上限（高门槛彩蛋 1~2 条）
TIER3_PAGE_TURN_DURATION_MS = 1000     # 翻页动画时长
TOAST_TIER3_UNLOCK = "一段尘封的记忆被唤醒了……"

# --- 批注淘汰规则 ---
TOAST_COMMENT_EVICTED = "一段更久远的记忆被覆盖了……"
EVICTION_BREATH_DURATION_MS = 4500     # 淘汰呼吸动画（放慢，温柔遗忘）

# ========== 动态光影 ==========
LIGHT_SWEEP_CENTER_X_AMPLITUDE = 0.30   # 光心水平移动范围（画布宽比例）
LIGHT_SWEEP_CENTER_Y_BASE = 0.35        # 光心垂直位置（相对画布高）
LIGHT_SWEEP_RADIUS = 0.45               # 光斑半径（画布对角线比例）
# 浅色：暖白窗光，提高最大不透明度并改用略带暖意的白，使浅色画布上也能察觉（此前0.07几乎融入米色）
LIGHT_SWEEP_COLOR = "#FFF6E0"
LIGHT_SWEEP_ALPHA_MAX = 0.12
# 深色模式专用：极近暗底的颜色 + 极低不透明度，仅留极淡呼吸层次而非突兀亮斑
LIGHT_SWEEP_COLOR_DARK = "#2E3340"      # 冷调月光柔光（与画布暗底融为一体）
LIGHT_SWEEP_ALPHA_MAX_DARK = 0.06       # 深色模式极克制（浅色 0.12 的 50%）

# ========== 封存复古滤镜 ==========
SEALED_OVERLAY_COLOR = "#D4C8B0"        # 牛皮纸遮罩色
SEALED_OVERLAY_ALPHA = 0.15
SEALED_VIGNETTE_INTENSITY = 0.35        # 暗角强度

# ========== 深色模式 ==========
DARK_BG = "#2C2A27"                     # 深棕灰，不用冷黑（需求文档规定全局背景）
DARK_BG_CANVAS = "#332E28"
DARK_TEXT = "#D8CEC0"
DARK_HINT = "#8C8278"
DARK_BUTTON_BG = "#3C362C"             # 哑光深棕
DARK_BUTTON_HOVER = "#4A4234"          # 悬停略亮
DARK_BUTTON_TEXT = "#D8CEBE"           # 暖米字

# ========== 沉浸式 UI 透明度 ==========
UI_OPACITY_HOVER = 0.96                 # 鼠标靠近清晰显示
UI_OPACITY_FULLSCREEN = 0.06            # 全屏近乎隐形
UI_HOVER_ZONE = 60                      # 鼠标距顶部/底部多少像素触发显形

# ========== 弹窗磨砂参数 ==========
DIALOG_BG_COLOR = "#ECE6D8"   # 协调暖米（与纸色同源，解决米色+深棕不协调）
DIALOG_BG_ALPHA = 0.92

# ========== 文风选项（文档规定三套 prompt） ==========
TONE_OPTIONS = [
    ("治愈",   "旧时光留下的温柔碎语"),
    ("丧系",   "残留的淡淡遗憾"),
    ("搞笑",   "旧主人调皮的碎碎念"),
]

# ========== 页眉题记（多段轮换） ==========
EPIGRAPHS = [
    "文字如落叶，终将归于尘土。但在飘落之前，它们曾见过光。",
    "每一笔都是告别，每一划都是重逢。",
    "遗忘不是消失，是被时间轻轻收起。",
    "写下来，不为记住，只为此刻。",
    "纸上的墨迹会淡，心里却留下了一小块影子。",
    "没有什么是永久的——正因如此，一切才珍贵。",
    "这是一面会记住、也会忘记的镜子。",
]

# ========== 不同场景的空画布提示 ==========
EMPTY_HINTS = [
    "这儿很安静，适合安放一段心事。",
    "白纸在等你，它什么都不会说，什么都愿意听。",
    "不必完美，哪怕是几个字，也是一次抵达。",
    "写下第一笔，记忆就有了形状。",
    "一张空白的纸，就像一个还没开始的故事。",
    "笔尖落下的地方，时光会往回走一步。",
    "纸已备好，只差一颗愿意落笔的心。",
    "现在写下的字，会在某个黄昏慢慢淡去。",
    "你写下，它存在。片刻也好。",
    "纸比人久长——但你写下的那个瞬间，它只属于你。",
    "有些话，不写下来就真的没了。",
]

# 「曾写过、如今字全散尽」专属空状态文案：给遗忘一个回响，区别于"从未写过"的通用邀请
EMPTY_HINTS_FADED = [
    "你写下的，都走远了。纸又空了。",
    "它们来过，又都忘了你。",
    "这一页的字，最后都安心地散了。",
    "墨痕散尽，只剩纸还记得你来过。",
    "你曾在此停留，如今连痕迹也凉了。",
    "写下的终会淡去——这一次，是真的空了。",
    "它们陪了你一阵，然后谁也没留住谁。",
    "空白回来了，带着你刚失去的温度。",
    "故事写过，也忘了。纸还是那张纸。",
    "你松了手，它们便慢慢不见了。",
]

# ========== 悬浮提示小字 ==========
TOAST_REVIVED = "它感受到了你的注视，暂时不会离开。"
TOAST_REVIVE_CAPPED = "它已经很累了，不再回应你的注视。"
TOAST_REVIVE_LAST = "这是最后一次能挽留它了，再凝视也无法让它回应了。"
TOAST_DISSOLVE_FINAL = "它陪了你很久，你也曾努力留住它，如今终于安心地散去了。"
# 续命梯度文案：随续命次数递减，呼应「字越续越难被唤回」。
# 索引对应 new_rc（1~5），第 1 次恢复最强、第 5 次几近消散。
REVIVE_TOASTS = [
    "它重新睁开了眼，似乎认出了你。",
    "它又转过头来，在你的注视里多留了一会儿。",
    "它微微动了动，却还是更想睡去。",
    "它轻轻应了一声，呼吸已很浅了。",
    "它最后颤了颤，几乎要散在风里了。",
]
TOAST_DELETED = "字迹消散如灰，不必挂念。"
TOAST_EXPORTED = "此刻被定格成永恒。"
TOAST_NEW_PAGE = "又翻开了一页。新旧交替，朝朝暮暮。"
TOAST_COMMENT_ADDED = "陌生人的笔迹落在此处。"
TOAST_PURE_MODE = "只剩纸与字，和你。按 Esc 或 Ctrl+P 回来。"
TOAST_PURE_MODE_EXIT = "工具条回来了，像老朋友。"
TOAST_DARK_ON = "灯暗了，纸还在。"
TOAST_DARK_OFF = "天亮了。"
TOAST_ATMOSPHERE_ON = "光影缓慢流转，尘埃轻轻飘落。"
TOAST_ATMOSPHERE_OFF = "归于素净。"
TOAST_STYLE_CHANGED = "纸上多了另一种声音。"
TOAST_UNSEALED = "封印解开了。那些褪色的字，又要开始远行了。"
TOAST_UNSEALING_PROGRESS = "封印在松动……"

# ========== 纸面积淀温度（写字越多、停留越久越暖） ==========
PAPER_WARMTH_PER_CHAR = 0.0003            # 每个字增加的暖色调偏移
PAPER_WARMTH_MAX = 0.30                   # 最大暖色调偏移
PAPER_WARMTH_PER_SECOND = 0.00002         # 每秒自然增加的暖色调偏移
PAPER_WARMTH_COOL_PER_SECOND = 0.003       # 全空(字散尽)时每秒冷却的暖色调偏移，约100s余温散尽

# ========== 空画布预置淡残影文案 ==========
GHOST_PHRASES = [
    "有些话不说出口，就变成了纸上的影子。",
    "曾经也有人坐在这里，写了几行字，然后走远了。",
    "旧时光并不走了——它只是变得很轻很轻。",
    "遗忘是一座安静的博物馆。",
    "每张纸都住过一个陌生人。",
    "风吹过纸页，字迹就淡了一层。",
    "你不必记得一切。有些东西，轻就够了。",
    "它等了你很久，久到纸边发了黄。",
    "不是空的——只是你看不见那些已经消散的字。",
    "一张纸的沉默，比任何记忆都重。",
]

# ========== 时辰感知残影（不同时辰显示不同内容，加深时间流逝感）==========
GHOST_PHRASES_DAWN = [
    "晨光把昨夜的梦晒成了薄雾。",
    "天还没全亮，纸上的字就已经醒了。",
    "露水从纸边渗进来——那是上一个黎明留下的。",
    "早安。上一任主人总是在五点四十分醒来。",
    "天亮之前写下的字，最容易消散。",
]
GHOST_PHRASES_DUSK = [
    "夕阳刚好落在这页纸的右下角。",
    "黄昏是纸最脆弱的时候——字也会想家。",
    "天要黑了。趁墨迹还没散尽，再看一眼。",
    "上一任主人习惯在黄昏写信，写完了也不寄。",
    "日落之后写下的，都带着告别的手势。",
]
GHOST_PHRASES_NIGHT = [
    "深夜的纸会自己叹息。",
    "凌晨两点，这张纸上曾有人哭过。",
    "灯光太暗，有些字看不清——也许不是看不清。",
    "夜晚的空白比白天的更重。",
    "失眠的人总会翻到这一页，什么也不写。",
    "窗外的月亮和纸上的月亮，哪一个更远。",
]

# ========== 引导页文案 ——— 文艺化重写 ==========
GUIDE_LINES = (
    "你翻开了一张纸。\n"
    "一张曾经属于某个陌生人的纸。\n\n"
    "它在时间里等了很久。\n"
    "等一双新的手，等一段新的心事。\n\n"
    "写下的每一个字都会变淡、泛黄、\n"
    "最后变成纸面上的一小片光。\n"
    "但只要你愿意凝视，\n"
    "它们会为你多停留一会儿。\n\n"
    "遗忘不是失败，是文字的呼吸。\n"
    "如同所有的故事，终将归于安静。\n\n"
    "现在，它归你了。"
)

# ========== 档案馆文案 ==========
ARCHIVE_SEARCH_PLACEHOLDER = "在旧纸张里寻找一个词语…"
ARCHIVE_WORDCLOUD_TITLE = "这些字，曾有人反复想起"
ARCHIVE_STATS_TITLE = "在你来之前，已经有字悄悄消散了"
ARCHIVE_EMPTY = "这里什么也没有。\n就像某些夜晚，某些心事。\n等有一天，你写下的字会在这里安家。"
ARCHIVE_CONFIRM_DELETE = "确定要让它归入遗忘吗？\n纸会变成空白，但时光不会。"
ARCHIVE_CONFIRM_SEAL = "封存之后，字迹不再褪去。\n但也不能再增添新的了。\n你准备好了吗？"

# ========== 导出文案 ==========
EXPORT_DIALOG_TITLE = "将这一刻，定格成永恒。"
EXPORT_EPIGRAPH_LABEL = "带上页眉那句诗"
EXPORT_FORMAT_LABEL = "以什么模样留下"
EXPORT_DPI_LABEL = "要看得清每一道笔触吗"

# ========== API 设置文案 ==========
API_DIALOG_TITLE = "接入豆包 · 让纸上有另一个人的声音"
API_DIALOG_HINT = "密钥只留在你的电脑里。\n字迹不会上传，秘密还是秘密。"
API_PLACEHOLDER = "写下密钥，像递一把钥匙…"

# ========== 小王子文字量级换算 ==========
PRINCE_LEVELS = [
    (0, "扉页空白，等待第一行字"),
    (100, "小王子遇见玫瑰之前"),
    (500, "小王子离开 B-612 那天"),
    (2500, "小王子抵达第七颗行星"),
    (5000, "小王子遇见了狐狸"),
    (12000, "小王子找到了水井"),
    (30000, "小王子回到了星星上"),
    (50000, "你写出了自己的星球"),
]

# ========== 纸张阶段 ==========
STAGE_LABELS = {
    "黄1": "新纸",
    "黄2": "微旧",
    "黄3": "泛黄",
    "黄4": "老纸",
    "封存": "封存",
}

STAGE_THRESHOLDS = [
    (3 * 86400, "黄1"),    # < 3 天 → 新纸
    (7 * 86400, "黄2"),    # 3~7 天 → 微旧
    (14 * 86400, "黄3"),   # 7~14 天 → 泛黄
    # ≥ 14 天 → 黄4 老纸（见 get_paper_stage 兜底返回）
]


def get_paper_stage(create_time: float, is_sealed: bool = False) -> str:
    """根据创建时间（Unix 秒）动态计算纸张老化阶段。

    注意：参数为创建时间戳，函数内部按当前时间算出"已存在秒数"再比对阈值，
    切勿直接传入绝对时间戳当作 age（否则 ~1.7e9 永远落在最老档）。
    """
    if is_sealed:
        return "封存"
    age_sec = max(0.0, time.time() - float(create_time))
    for threshold, stage in STAGE_THRESHOLDS:
        if age_sec < threshold:
            return stage
    return "黄4"


# ========== 快捷键 ==========
SHORTCUT_NEW = "Ctrl+N"
SHORTCUT_EXPORT = "Ctrl+E"
SHORTCUT_BACK = "Ctrl+W"
SHORTCUT_ARCHIVE = "Ctrl+Tab"
SHORTCUT_FULLSCREEN = "F11"
SHORTCUT_PURE_MODE = "Ctrl+P"
SHORTCUT_ATMOSPHERE = "Ctrl+Shift+A"
SHORTCUT_DARK_MODE = "Ctrl+D"

# ========== 快捷键列表（用于弹窗展示） ==========
SHORTCUTS = [
    ("Ctrl+N", "新建默认草稿纸笔记"),
    ("Ctrl+E", "快速打开导出图片面板"),
    ("Ctrl+W", "一键返回档案馆"),
    ("Ctrl+Tab", "呼出/收起档案馆侧边栏"),
    ("Ctrl+P", "纯画布模式"),
    ("Ctrl+Shift+A", "开关高级氛围"),
    ("Ctrl+D", "深色模式切换"),
    ("F11", "全屏/退出全屏"),
]

# ========== 杂项（兼容旧引用） ==========
# 首次启动/空白新页的占位示例文字（半透明，用户开始打字后淡出）
# 改为多句随机，避免每次新建/打开都显示同一句。
PLACEHOLDER_SAMPLES = [
    "去年冬天，我在窗边写下一些字，后来它们都消失了。现在轮到你。",
    "有些话没说出口，就成了纸上的灰。试着写点什么吧。",
    "你记得的，比你想的少；你忘记的，比你想的多。从这一句开始。",
    "风把旧信吹散了，但空白也是一封信。写给还没发生的自己。",
    "这里曾有人停笔，又有人提笔。现在，笔在你手里。",
    "忘记不是失去，是另一种收藏。写下此刻你不愿忘的。",
    "灯还亮着，字会慢慢凉。趁现在，把心里那句说出来。",
    "我们不擅长告别，却擅长想起。先写下一个名字也好。",
]
# 兼容旧引用：默认取第一句
PLACEHOLDER_SAMPLE = PLACEHOLDER_SAMPLES[0]

# 档案馆"已沉睡"页面：很久未打开时，悬浮提示一行小字
SLEEP_DAYS = 30
SLEEP_HINT_TEXT = "这张纸已经很久没人打开了，上面的文字正在缓慢消散。"

COMMENT_COLOR = "#8C887C"
COMMENT_COLOR_DARK = "#B0A080"          # 深色模式批注色：暖灰米，暗底上温润可辨
# 状态栏"批注 n/8"计数：比提示色更淡，向"手写脚注"靠拢，弱化 UI 标签感
COMMENT_COUNTER_COLOR = "#B8B4A8"
COMMENT_COUNTER_COLOR_DARK = "#C9C1AE"

# ========== 手写字体 ==========
# 默认手写字体取自 assets/fonts/ 下所有字体文件（加载逻辑见 canvas._load_local_fonts）
# 手写字体族候选（无本地/导入字体时改用系统书法字体，随机分配以暗示不同时期/人物）
HANDWRITING_FONT_FAMILIES = [
    "KaiTi", "STKaiti", "STXingkai", "FZYaoti", "FZShuTi", "LiSu",
    "Segoe Script", "Comic Sans MS", "Brush Script MT", "Ink Free",
]
COMMENT_GUTTER_RATIO = 0.26            # 批注两侧留白带占画布宽度比例（给批注更宽的空间）
COMMENT_BASE_ALPHA_MIN = 0.30          # 批注基础透明度下限（岁月褪色，固定 0.3~0.5）
COMMENT_BASE_ALPHA_MAX = 0.50

# ========== Toast 提示文案补充 ==========
TOAST_CACHE_CLEARED = "残影已拂去，字迹仍在。"
TOAST_FONT_FALLBACK = "手写体未找到，换了一支笔。"
TOAST_DATA_CORRUPT = "这张纸有些看不清了，要丢掉吗？"
TOAST_PERFORMANCE_ON = "纸面素净了些，更轻快了。"
TOAST_PERFORMANCE_OFF = "质感回来了，尘埃依旧飘落。"

# ========== 主窗口边框（深浅双色，绘制于主窗口 paintEvent，稳定不闪烁；直角矩形，无圆角） ==========
WINDOW_BORDER_DARK = (74, 68, 58)     # 比暗框略亮，深色模式清晰可见
WINDOW_BORDER_LIGHT = (160, 156, 148)  # 柔和暖灰，浅色模式下可见但不再偏深棕
BORDER_OPACITY_LOW = 0.18              # 窗口边框常态：半透明，几乎隐于纸面
BORDER_OPACITY_HOVER = 0.55            # 窗口边框悬停：清晰可见

# ========== 性能分级 ==========
class PerfTier:
    """性能档位：依据电脑性能自适应粒子/纹理开销。"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

PERF_TIER_MULTIPLIER = {
    PerfTier.LOW: 0.30,
    PerfTier.MEDIUM: 0.65,
    PerfTier.HIGH: 1.00,
}

# 粒子/纹理与窗口面积的映射系数（面积 / 除数 = 粒子数上限，HIGH 档基准，1280×720 窗口 ≈ 原版固定值）
DUST_AREA_DIVISOR = 22000          # 单位像素²/每粒尘（值越小粒子越多；略低于 30000 使尘埃稍多）
GHOST_AREA_DIVISOR = 46000         # 残影斑单位像素²/每斑（原固定值 20）
STAR_AREA_DIVISOR = 6200           # 星场单位像素²/每星（原固定值 150）
PAPER_CACHE_REFRESH_INTERVAL = 2.0 # 静态纹理缓存刷新间隔（秒，纤维微动）

# ========== 色彩体系统一常量（消除各处散落硬编码色值） ==========

# --- 画布绘制层 ---
CANVAS_BORDER_COLOR_DARK = "#9A9384"          # 深色模式画布内容区域细框
CANVAS_BORDER_COLOR_LIGHT = "#DBD3C5"         # 浅色模式画布内容区域细框
PAGE_CONTENT_BG_DARK = (26, 24, 21)           # 深色模式页面内容底色
PAGE_CONTENT_BG_LIGHT = (245, 241, 232)       # 浅色模式页面内容底色

# --- 飘落尘埃粒子双模式色 ---
# 浅色底(米白 #F6F3E9)用柔和浅暖灰，深色底(深棕 #332E28)用明亮暖白灰：
# 两者均与各自底色拉开对比度但不抢眼，做到"真区分、肉眼可见、克制不刺眼"。
DUST_COLOR_LIGHT = (160, 149, 130)           # 浅色模式尘埃：米白纸上的浅暖灰落尘
DUST_COLOR_DARK = (182, 172, 156)            # 深色模式尘埃：暗底上反光的暖白微尘

# --- 封存视觉叠层（撕裂纸边、sepia 泛黄、颗粒） ---
SEALED_GRAIN_RGB_DARK = (60, 40, 20)          # 深色模式颗粒色
SEALED_GRAIN_RGB_LIGHT = (80, 60, 40)         # 浅色模式颗粒色
SEALED_GRAIN_ALPHA = 18                       # 颗粒透明度
SEALED_OVERLAY_LIGHT_RGB = (130, 100, 70)     # 浅色模式牛皮纸覆层色
SEALED_OVERLAY_LIGHT_ALPHA = 60               # 浅色模式覆层透明度
SEALED_LOWLIGHT_RGB = (64, 50, 35)            # 深色模式暗部覆层色
SEALED_SEPIA_LIGHT = "#E8D8B0"               # 浅色 sepia 叠色
SEALED_SEPIA_DARK = "#3A2E20"                # 深色 sepia 叠色
SEALED_HIGHLIGHT_LIGHT = "#F0E6C8"            # 浅色撕裂纤维高光
SEALED_HIGHLIGHT_DARK = "#3A3020"             # 深色撕裂纤维高光
SEALED_HALO_LIGHT = "#F8E8C0"                # 浅色解封光圈
SEALED_HALO_DARK = "#E8C880"                 # 深色解封光圈
SEALED_FILL_EDGE = "#353025"                 # 深色模式封存卡片底色
SEALED_FILL_EDGE_LIGHT = "#F0E9C8"           # 浅色模式封存卡片底色

# --- 文字发光晕色 ---
TEXT_HALO_RGB_DARK = (165, 135, 82)           # 浅色模式文字柔光（深底用暗色）
TEXT_HALO_RGB_LIGHT = (215, 195, 155)         # 实际是浅色模式下 halo 色（原先 165, 135, 82 在浅色底上不可见，改为偏亮）

# --- 临终灰度偏移 ---
TEXT_GRAYSCALE_THRESHOLD = 0.20               # 透明度低于此值开始灰度偏移
TEXT_GRAYSCALE_MAX_FACTOR = 0.75              # 最大灰度混合比例（0=无色偏, 1=全灰）

# --- 翻页动画 ---
PAGE_TURN_COLOR = (255, 245, 220)             # 翻页光晕色

# --- 毛玻璃雾面星场 ---
STAR_COUNT = 150                               # 星场星点默认数量
STAR_LIGHT_COLOR = (232, 230, 222)            # 星场微光（浅色模式）

# --- 工具栏颜色（原散落在 toolbar.py 各处） ---
TOOLBAR_BG_RGB = (44, 42, 39)                 # 工具栏背景色
EPIGRAPH_COLOR_LIGHT = "#7C7768"              # 浅色模式页眉题记文字
EPIGRAPH_HOVER_LIGHT = "#CFC6B5"              # 浅色模式页眉题记悬停
EPIGRAPH_COLOR_DARK = "#B3A998"               # 深色模式页眉题记文字

# --- 档案馆颜色 ---
ARCHIVE_BG_RGB = (212, 202, 182)              # 档案馆浅色背景 RGB
ARCHIVE_CARD_TEXT = "#4A453B"                 # 卡片文字色（与 TEXT_COLOR 同源暖棕）
ARCHIVE_SEARCH_BG = "rgba(228,223,210,0.6)"   # 搜索框背景
ARCHIVE_SCROLLBAR_HANDLE = "#D9D3C5"          # 滚动条手柄
ARCHIVE_SLEEP_OVERLAY = "rgba(40, 38, 34, 0.82)"  # 沉睡页覆盖层
ARCHIVE_DIALOG_BG = "#ECE6D8"                  # 弹窗背景（与 DIALOG_BG_COLOR 一致）
ARCHIVE_WORDCLOUD_WORD = "#4A453B"             # 词云字色
ARCHIVE_STATS_SUBTITLE = "#8C8478"             # 统计副标题浅色
ARCHIVE_CARD_AGED = "#F0E8C8"                 # 老化卡片底色
ARCHIVE_BUTTON_TEXT = "#5A5548"                # 卡片按钮文字色
ARCHIVE_BUTTON_TEXT_DARK = "#D8CEBE"           # 卡片按钮深色模式文字色
COMMENT_INK_LIGHT = "#5A5548"                  # 浅色模式批注墨迹底色
COMMENT_INK_DARK = "#B0A080"                   # 深色模式批注墨迹底色
