"""
《未完成·遗忘》辅助函数 —— 氛围升级版。
墨水氧化色阶、尘埃粒子、纸张质感随机种子。
"""
import math
import time
import random
from typing import Tuple, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QImage

from utils.constants import (
    LIFE_BASE_SEC, LIFE_MAX_SEC,
    LIFE_DECAY_WARN_RATIO, LIFE_END_WARN_RATIO,
    LIFE_DYING_RATIO, LIFE_DYING_DURATION_SEC,
    AFTERGLOW_DURATION_SEC, AFTERGLOW_MAX_ALPHA,
    REVIVE_BONUS_GRADIENT, REVIVE_MAX_COUNT,
    INK_FRESH, INK_OXIDIZED_1, INK_OXIDIZED_2, INK_OXIDIZED_3, INK_GHOST,
    DUST_PARTICLE_COUNT, DUST_PARTICLE_MAX,
    DUST_PARTICLE_RADIUS_MIN, DUST_PARTICLE_RADIUS_MAX,
    DUST_PARTICLE_BASE_SPEED, DUST_COLORS,
    DURATION_DISSOLVE_PARTICLE,
    GHOST_TEXT_COLOR, TEXT_COLOR,
    FIBER_LINE_COUNT, FIBER_COLOR_BASE, FIBER_ALPHA_MAX, FIBER_DRIFT_AMPLITUDE,
    STAIN_COUNT, STAIN_COLORS, STAIN_ALPHA_MAX, STAIN_RADIUS_MIN, STAIN_RADIUS_MAX,
    CREASE_COUNT, CREASE_COLOR, CREASE_ALPHA, CREASE_WIDTH,
    PerfTier, PERF_TIER_MULTIPLIER,
    DUST_AREA_DIVISOR, GHOST_AREA_DIVISOR, STAR_AREA_DIVISOR,
    TEXT_GRAYSCALE_THRESHOLD, TEXT_GRAYSCALE_MAX_FACTOR,
    DAYNIGHT_DAWN_COLOR, DAYNIGHT_NOON_COLOR,
    DAYNIGHT_DUSK_COLOR, DAYNIGHT_NIGHT_COLOR, BG_YELLOW_1,
)


# ========== 文字生命周期 ==========

def compute_alpha(create_timestamp: float, life_total_sec: float,
                  revive_count: int = 0, current_time: Optional[float] = None) -> float:
    """
    返回 0.0（完全消散）~ 1.0（鲜墨）的文字不透明度。
    续命可减缓淡化速度。
    新增：弥留阶段缓动消融，禁止突兀消失。
    """
    if current_time is None:
        current_time = time.time()
    age = max(0, current_time - create_timestamp)
    if life_total_sec <= 0:
        life_total_sec = LIFE_BASE_SEC
    
    ratio = age / life_total_sec
    
    if ratio <= (1.0 - LIFE_END_WARN_RATIO):
        return 1.0 - ratio
    
    if ratio <= (1.0 - LIFE_DYING_RATIO):
        warning_range = LIFE_END_WARN_RATIO - LIFE_DYING_RATIO
        warning_progress = (ratio - (1.0 - LIFE_END_WARN_RATIO)) / (LIFE_END_WARN_RATIO - LIFE_DYING_RATIO)
        return LIFE_END_WARN_RATIO - warning_progress * warning_range
    
    if ratio <= 1.0:
        dying_start_ratio = 1.0 - LIFE_DYING_RATIO
        dying_progress = (ratio - dying_start_ratio) / LIFE_DYING_RATIO
        return LIFE_DYING_RATIO * (1.0 - dying_progress)
    
    dying_elapsed = (age - life_total_sec) / LIFE_DYING_DURATION_SEC
    if dying_elapsed >= 1.0:
        return 0.0
    return LIFE_DYING_RATIO * (1.0 - dying_elapsed ** 2)


def is_word_alive(create_timestamp: float, life_total_sec: float,
                  revive_count: int = 0, current_time: Optional[float] = None) -> bool:
    """文字是否仍有可见痕迹（alpha > 0）。"""
    return compute_alpha(create_timestamp, life_total_sec, revive_count, current_time) > 0.0


def get_word_warning_stage(create_timestamp: float, life_total_sec: float,
                           revive_count: int = 0, current_time: Optional[float] = None) -> int:
    """返回当前预警阶段：0=正常, 1=衰退预警(寿命耗尽≥75%), 2=临终预警(寿命耗尽≥90%)。
    两段预警给用户预留更长的挽留窗口：衰退期字开始明显褪色但不危急，
    临终期才进入真正倒计时。"""
    if current_time is None:
        current_time = time.time()
    if life_total_sec <= 0:
        return 2  # 异常短寿命直接进临终
    age = max(0.0, current_time - create_timestamp)
    ratio = age / life_total_sec
    if ratio >= 1.0:
        return 2
    if ratio >= (1.0 - LIFE_END_WARN_RATIO):
        return 2
    if ratio >= (1.0 - LIFE_DECAY_WARN_RATIO):
        return 1
    return 0




def revive_word(create_timestamp: float, life_total_sec: float,
                revive_count: int, current_time: Optional[float] = None) -> Tuple[float, float, int]:
    """
    续命操作：按次递进式衰减，ratio 不会归零。
    每一次续命将文字拉回到梯度递减的目标 ratio，寿命按梯度递增。
    梯度 lifespan bonus：REVIVE_BONUS_GRADIENT = 172800/86400/43200/14400/7200（秒，约2/1/0.5/0.167/0.083天）。
    梯度 ratio 拉回：0.35/0.50/0.60/0.70/0.80。
    ≥6次仅提亮不增加寿命。
    返回 (new_create_ts, new_life_total, new_revive_count)。
    """
    if current_time is None:
        current_time = time.time()
    new_revive = revive_count + 1
    # ≥6次：仅提亮，不增加寿命、不计数（保持原值）
    if new_revive > REVIVE_MAX_COUNT:
        return create_timestamp, life_total_sec, revive_count
    # 计算当前年龄比例
    age = max(0.0, current_time - create_timestamp)
    current_ratio = age / life_total_sec if life_total_sec > 0 else 1.0
    # 按次递进的目标 ratio：第 1 次最多恢复（→0.35），第 5 次几乎不恢复（→0.80）
    target_ratios = [0.35, 0.50, 0.60, 0.70, 0.80]
    target_ratio = target_ratios[new_revive - 1]
    # 不应让当前已经很鲜活的字反向老化
    target_ratio = min(target_ratio, current_ratio)
    # 寿命按梯度继续累加
    bonus = REVIVE_BONUS_GRADIENT[new_revive - 1]
    new_life = min(life_total_sec + bonus, LIFE_MAX_SEC)
    # 反推 create_timestamp，使续命后 age 比例固定在 target_ratio
    new_create_ts = current_time - target_ratio * new_life
    return new_create_ts, new_life, new_revive


# ========== 墨水氧化色阶 ==========

def get_ink_oxidation_color(alpha: float, base_color_hex: str = TEXT_COLOR,
                            is_dark_mode: bool = False) -> QColor:
    """
    根据不透明度（0完全消散→1鲜墨），返回对应氧化阶段的墨水颜色。
    文字褪色不再单纯透明，而分阶段做墨迹氧化泛黄、笔画残缺效果。
    """
    if is_dark_mode:
        # 深色模式下文字整体为浅色系，叠加在暗底上方才可见。
        # 关键：氧化(淡化)阶段保持浅亮，临终最亮(浅暖白)，
        # 否则低 alpha 的深褐会融入暗底而肉眼不可见(浅色模式反之用深褐才可见)。
        if alpha >= 0.90:
            c = QColor("#D8CEC0")
        elif alpha >= 0.70:
            c = QColor("#CDC1A0")
        elif alpha >= 0.40:
            c = QColor("#C2B690")
        elif alpha >= 0.15:
            c = QColor("#CABDA0")
        else:
            c = QColor("#DCD4C2")  # 临终：浅暖白，暗底上清晰可辨
    else:
        if alpha >= 0.90:
            c = QColor(INK_FRESH)
        elif alpha >= 0.70:
            # 微氧化：鲜墨→微褐
            t = (0.90 - alpha) / 0.20
            c = _lerp_color(QColor(INK_FRESH), QColor(INK_OXIDIZED_1), t)
        elif alpha >= 0.40:
            # 中度氧化
            t = (0.70 - alpha) / 0.30
            c = _lerp_color(QColor(INK_OXIDIZED_1), QColor(INK_OXIDIZED_2), t)
        elif alpha >= 0.15:
            # 深度氧化
            t = (0.40 - alpha) / 0.25
            c = _lerp_color(QColor(INK_OXIDIZED_2), QColor(INK_OXIDIZED_3), t)
        else:
            # 即将消散
            t = (0.15 - alpha) / 0.15
            c = _lerp_color(QColor(INK_OXIDIZED_3), QColor(INK_GHOST), t)

    c.setAlpha(int(max(0.0, min(1.0, alpha)) * 255))
    return c


def _lerp_color(a: QColor, b: QColor, t: float) -> QColor:
    """线性插值两个 QColor。"""
    t = max(0, min(1, t))
    return QColor(
        int(a.red() + (b.red() - a.red()) * t),
        int(a.green() + (b.green() - a.green()) * t),
        int(a.blue() + (b.blue() - a.blue()) * t),
        int(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


# ========== 笔画残缺模拟 ==========

def get_eroded_alpha(alpha: float, seed: float = 0.0) -> float:
    """
    模拟笔画残缺：在透明度的基础上，叠加微小随机波动，
    使文字边缘不均匀褪色，产生"笔画零落"的视觉效果。
    seed 可用文字位置/内容哈希产生。
    """
    if alpha >= 0.90:
        return min(1.0, alpha)  # 鲜墨不残缺（但呼吸动画可能把 alpha 推到 >1.0）
    # 残缺强度随淡化加剧
    erosion_strength = (1.0 - alpha) * 0.35
    # 用 seed 产生确定性随机波动，避免帧间抖动太大
    noise = (math.sin(seed * 127.1 + 311.7) * 0.5 +
             math.sin(seed * 269.5 + 183.3) * 0.3 +
             math.sin(seed * 431.9 + 731.1) * 0.2)
    erosion = noise * erosion_strength
    result = alpha - abs(erosion)
    return max(0, min(1, result))


# ========== 呼吸动画 alpha 调制 ==========

def breathing_alpha_for_display(word_alpha: float, current_time: float,
                               cycle_duration_ms: float = 3000.0,
                               is_warning: bool = False) -> float:
    """
    在基础 alpha 上叠加正弦呼吸效果。
    使用 cos 实现缓缓呼吸的起伏感。
    is_warning=True 时进入临终预警：透明度在 0.6~0.9 之间缓慢脉动
    （需求文档规定，回光返照般抓住即将消逝的文字）。
    新增：弥留阶段呼吸更缓慢、振幅更小。
    """
    if word_alpha <= 0:
        return 0
    
    if word_alpha <= LIFE_DYING_RATIO:
        dying_cycle = cycle_duration_ms * 3
        phase = (current_time * 1000 % dying_cycle) / dying_cycle
        breath = (math.cos(phase * 2.0 * math.pi) + 1.0) * 0.5
        amplitude = min(word_alpha * 0.05, 0.02)
        return word_alpha + amplitude * (breath - 0.5)
    
    phase = (current_time * 1000 % cycle_duration_ms) / cycle_duration_ms
    breath = (math.cos(phase * 2.0 * math.pi) + 1.0) * 0.5  # 0~1
    
    if is_warning:
        # 回光返照：进入预警(剩余 10%)后，透明度从当前低点平滑抬升到回光峰值，
        # 再随寿命令尽平滑归零——消除原“剩余 10% 处从 ~0.10 硬跳到 0.75”的突兀一跳，
        # 让文字像残烛般温柔明灭后悄然消散，贴合“遗忘”主题。
        # t: 0(刚进入预警)→1(逼近弥留)；钟形 0→峰值→0 保证两端与前后阶段连续无跳。
        t = (LIFE_END_WARN_RATIO - word_alpha) / (LIFE_END_WARN_RATIO - LIFE_DYING_RATIO)
        t = max(0.0, min(1.0, t))
        glow = 0.55 * math.sin(t * math.pi)      # 平滑钟形回光
        return word_alpha + glow + 0.04 * (2.0 * breath - 1.0)  # 极缓呼吸微漾
    
    amplitude = min(word_alpha * 0.12, 0.10)
    return word_alpha + amplitude * (breath - 0.5)


def compute_afterglow_alpha(create_timestamp: float, life_total_sec: float,
                           current_time: Optional[float] = None) -> float:
    """
    计算文字完全消散后的残影透明度。
    文字彻底消失后，短时间保留极淡残影，随后缓缓抹去。
    """
    if current_time is None:
        current_time = time.time()
    age = max(0, current_time - create_timestamp)
    if life_total_sec <= 0:
        life_total_sec = LIFE_BASE_SEC
    
    fade_start = life_total_sec + LIFE_DYING_DURATION_SEC
    
    if age < fade_start:
        return 0.0
    
    afterglow_time = (age - fade_start) / AFTERGLOW_DURATION_SEC
    
    if afterglow_time >= 1.0:
        return 0.0
    
    return AFTERGLOW_MAX_ALPHA * (1.0 - afterglow_time ** 1.5)


# ========== 尘埃粒子系统 ==========

class DustParticle:
    """单个漂浮尘埃粒子。"""
    __slots__ = ('x', 'y', 'radius', 'color', 'vx', 'vy',
                 'alpha', 'alpha_dir', 'seed')

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.radius = random.uniform(DUST_PARTICLE_RADIUS_MIN, DUST_PARTICLE_RADIUS_MAX)
        self.color = random.choice(DUST_COLORS)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.3, 1.0) * DUST_PARTICLE_BASE_SPEED
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(0, 3)  # 微微上扬
        self.alpha = random.uniform(0.18, 0.38)
        self.alpha_dir = 1
        self.seed = random.random() * 100

    def update(self, dt: float, w: float, h: float):
        """更新粒子位置（带边界反弹和透明度呼吸）。"""
        self.x += self.vx * dt
        self.y += self.vy * dt
        # 边界反弹
        margin = 20
        if self.x < -margin:
            self.x = w + margin
        if self.x > w + margin:
            self.x = -margin
        if self.y < -margin:
            self.y = h + margin
        if self.y > h + margin:
            self.y = -margin
        # alpha 呼吸（v2：抬高基线，避免"肉眼不可见"）
        self.alpha += self.alpha_dir * random.uniform(0.001, 0.004)
        if self.alpha > 0.45:
            self.alpha_dir = -1
        elif self.alpha < 0.18:
            self.alpha_dir = 1


def generate_dust_particles(w: float, h: float, count: int | None = None) -> List[DustParticle]:
    """在画布范围内生成随机漂浮尘埃粒子。"""
    if count is None:
        count = DUST_PARTICLE_MAX
    particles = []
    for _ in range(count):
        x = random.uniform(0, w)
        y = random.uniform(0, h)
        particles.append(DustParticle(x, y))
    return particles


# ========== 文字消散粒子 ==========

class DissolveParticle:
    """文字消散时拆解的粒子。"""
    __slots__ = ('x', 'y', 'radius', 'color', 'vx', 'vy',
                 'alpha', 'lifetime', 'age', 'seed', 'spin', 'drift_phase')

    def __init__(self, x: float, y: float, color_hex: str):
        self.x = x
        self.y = y
        # 增加粒子大小范围，更丰富的尘埃效果
        self.radius = random.uniform(0.8, 3.5)
        # 黄褐色调，增加更多颜色变化
        base = QColor(color_hex)
        variant = QColor(
            min(255, base.red() + random.randint(-25, 40)),
            min(255, base.green() + random.randint(-15, 30)),
            max(0, base.blue() + random.randint(-40, 15)),
        )
        self.color = variant.name()
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 15)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(8, 25)  # 更强向上飘动
        self.alpha = random.uniform(0.4, 0.85)
        self.lifetime = random.uniform(3.5, 7.0)  # 更长生命周期
        self.age = 0.0
        self.seed = random.random() * 100
        self.spin = random.uniform(-0.1, 0.1)  # 旋转角度
        self.drift_phase = random.uniform(0, 2 * math.pi)  # 漂移相位

    def update(self, dt: float) -> bool:
        """返回 True 表示粒子已消亡。"""
        self.age += dt
        if self.age >= self.lifetime:
            return True
        progress = self.age / self.lifetime
        
        # 基础运动：速度随时间减慢
        self.x += self.vx * dt * (1 - progress * 0.6)
        self.y += self.vy * dt * (1 - progress * 0.4)
        
        # 增加随机漂移，模拟气流影响
        drift_speed = 0.5 + progress * 1.5
        self.x += math.sin(self.drift_phase + self.age * 2) * drift_speed * dt
        self.y += math.cos(self.drift_phase + self.age * 1.5) * drift_speed * dt
        
        # 后期 alpha 衰减加速，更自然的消散
        if progress > 0.5:
            decay_rate = (progress - 0.5) / 0.5
            self.alpha *= (1 - decay_rate * dt * 3)
        self.alpha = max(0, self.alpha)
        return self.alpha <= 0.01


def generate_dissolve_particles(x: float, y: float, color_hex: str = INK_GHOST,
                                count: int | None = None) -> List[DissolveParticle]:
    """在指定位置生成文字消散粒子。"""
    if count is None:
        count = DUST_PARTICLE_COUNT
    particles = []
    for _ in range(count):
        ox = x + random.uniform(-8, 8)
        oy = y + random.uniform(-6, 6)
        particles.append(DissolveParticle(ox, oy, color_hex))
    return particles


# ========== 动态粒子管控 & 临终灰度 ==========

def compute_particle_limits(width: float, height: float, tier: str = PerfTier.HIGH):
    """依据窗口尺寸和性能档位动态计算各类粒子上限。

    Returns:
        dict: keys 'dust', 'ghost', 'star', 'dissolve_max'
    """
    area = width * height
    mult = PERF_TIER_MULTIPLIER.get(tier, 1.0)

    dust = max(3, int(area / DUST_AREA_DIVISOR * mult))
    ghost = max(2, int(area / GHOST_AREA_DIVISOR * mult))
    star = max(5, int(area / STAR_AREA_DIVISOR * mult))
    dissolve_max = max(15, int(dust * 1.8))

    return {
        'dust': dust,
        'ghost': ghost,
        'star': star,
        'dissolve_max': dissolve_max,
    }


def get_dying_grayscale_color(ink_color: QColor, base_alpha: float) -> QColor:
    """消失前墨迹灰度偏移：墨水氧化→褪色→灰化的观感。

    base_alpha:  文字当前剩余透明度（0=死亡, 1=鲜活）
    仅在 base_alpha <= TEXT_GRAYSCALE_THRESHOLD 时生效。
    """
    if base_alpha > TEXT_GRAYSCALE_THRESHOLD:
        return QColor(ink_color)

    # 从阈值到 0 之间的线性进度
    t = 1.0 - (base_alpha / TEXT_GRAYSCALE_THRESHOLD)  # 0→1 越接近死亡越灰
    gray = int(ink_color.red() * 0.299 + ink_color.green() * 0.587 + ink_color.blue() * 0.114)
    factor = t * TEXT_GRAYSCALE_MAX_FACTOR  # 最大灰度混合比例

    r = int(ink_color.red() * (1 - factor) + gray * factor)
    g = int(ink_color.green() * (1 - factor) + gray * factor)
    b = int(ink_color.blue() * (1 - factor) + gray * factor)

    return QColor(r, g, b, ink_color.alpha())


# ========== 纸纤维纹理生成 ==========

class FiberLine:
    """单根纸纤维。"""
    __slots__ = ('x1', 'y1', 'x2', 'y2', 'alpha', 'seed')

    def __init__(self, x1, y1, x2, y2, alpha, seed):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.alpha = alpha
        self.seed = seed


def generate_fiber_lines(w: float, h: float, seed: int = 42) -> List[FiberLine]:
    """生成纸纤维纹理线条列表。"""
    rng = random.Random(seed)
    fibers = []
    for _ in range(FIBER_LINE_COUNT):
        # 横向为主，微斜
        y = rng.uniform(3, h - 3)
        x1 = rng.uniform(-w * 0.3, w * 1.3)
        length = rng.uniform(w * 0.15, w * 0.70)
        angle = (rng.random() - 0.5) * 0.15  # 微斜
        x2 = x1 + length * math.cos(angle)
        y2 = y + length * math.sin(angle)
        alpha = rng.uniform(0.01, FIBER_ALPHA_MAX)
        fibers.append(FiberLine(x1, y, x2, y2, alpha, rng.random() * 200))
    return fibers


# ========== 黄斑位置 ==========

class StainSpot:
    """黄斑/水渍。"""
    __slots__ = ('x', 'y', 'radius', 'color', 'alpha')

    def __init__(self, x, y, radius, color, alpha):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.alpha = alpha


def generate_stains(w: float, h: float, seed: int = 99) -> List[StainSpot]:
    """在画布上生成随机黄斑/水渍。"""
    rng = random.Random(seed)
    stains = []
    for _ in range(STAIN_COUNT):
        x = rng.uniform(20, w - 20)
        y = rng.uniform(20, h - 20)
        radius = rng.uniform(STAIN_RADIUS_MIN, STAIN_RADIUS_MAX)
        color = rng.choice(STAIN_COLORS)
        alpha = rng.uniform(0.02, STAIN_ALPHA_MAX)
        stains.append(StainSpot(x, y, radius, color, alpha))
    return stains


# ========== 折痕线 ==========

class CreaseLine:
    """纸张折痕。"""
    __slots__ = ('x1', 'y1', 'x2', 'y2', 'alpha')

    def __init__(self, x1, y1, x2, y2, alpha):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.alpha = alpha


def generate_creases(w: float, h: float, seed: int = 77) -> List[CreaseLine]:
    """生成纸张折痕。"""
    rng = random.Random(seed)
    creases = []
    for _ in range(CREASE_COUNT):
        # 随机水平或垂直折痕
        if rng.random() > 0.5:
            y = rng.uniform(h * 0.15, h * 0.85)
            x1 = rng.uniform(0, w * 0.3)
            x2 = rng.uniform(w * 0.7, w)
            creases.append(CreaseLine(x1, y, x2, y, rng.uniform(0.01, CREASE_ALPHA)))
        else:
            x = rng.uniform(w * 0.15, w * 0.85)
            y1 = rng.uniform(0, h * 0.3)
            y2 = rng.uniform(h * 0.7, h)
            creases.append(CreaseLine(x, y1, x, y2, rng.uniform(0.01, CREASE_ALPHA)))
    return creases


# ========== 纸面细颗粒（纸齿质感）==========

_PAPER_GRAIN_CACHE: dict = {}


def get_paper_grain(tile: int = 320, seed: int = 2024) -> QImage:
    """
    生成程序化纸张细颗粒贴图（"纸齿"质感），模块级缓存，全局复用。
    像素多为透明，少量暗/亮颗粒，叠加到低透明度画布上形成细腻纸面肌理。
    """
    key = (tile, seed)
    cached = _PAPER_GRAIN_CACHE.get(key)
    if cached is not None:
        return cached

    rng = random.Random(seed)
    img = QImage(tile, tile, QImage.Format_ARGB32)
    img.fill(0)
    dark = QColor(74, 64, 48)     # 纸齿阴影（暖褐）
    light = QColor(255, 252, 244)  # 纸齿高光（暖白）
    for y in range(tile):
        for x in range(tile):
            r = rng.random()
            if r < 0.42:
                dark.setAlpha(rng.randint(0, 26))
                img.setPixelColor(x, y, dark)
            elif r < 0.60:
                light.setAlpha(rng.randint(0, 18))
                img.setPixelColor(x, y, light)
            # 其余像素保持透明
    _PAPER_GRAIN_CACHE[key] = img
    return img


# ========== 小王子文字量级换算 ==========

def prince_level_text(char_count: int) -> str:
    """将字数换算为小王子故事阶段描述。"""
    from utils.constants import PRINCE_LEVELS
    for threshold, text in reversed(PRINCE_LEVELS):
        if char_count >= threshold:
            return text
    return PRINCE_LEVELS[0][1]


# ========== 昼夜时辰感知 ==========

def get_day_period(hour: int | None = None) -> str:
    """
    根据当前小时返回时辰段。
    dawn: 5:00-8:00  晨光初透
    day:  8:00-17:00 阳光铺满
    dusk: 17:00-20:00 黄昏低斜
    night: 20:00-5:00 灯下静谧
    """
    if hour is None:
        hour = time.localtime().tm_hour
    if 5 <= hour < 8:
        return "dawn"
    elif 8 <= hour < 17:
        return "day"
    elif 17 <= hour < 20:
        return "dusk"
    else:
        return "night"


def _get_daynight_tint_factor(hour: int | None = None) -> float:
    """
    返回昼夜色调混合因子 0~1。
    0 = 晨色调最强, 0.5 = 正午标准色, 1 = 深夜色调最强。
    在过渡时段（如 7-8点, 16-17点）平滑插值。
    """
    if hour is None:
        tm = time.localtime()
        hour = tm.tm_hour + tm.tm_min / 60.0
    else:
        hour = float(hour)

    if 5 <= hour < 8:
        # 晨：从夜过渡到午，5点=0.15, 8点=0.5
        return 0.15 + (hour - 5) / 3.0 * 0.35
    elif 8 <= hour < 17:
        # 昼：标准暖黄，中间微暖
        progress = (hour - 8) / 9.0  # 0 at 8h, 1 at 17h
        return 0.50 + math.sin(progress * math.pi) * 0.04
    elif 17 <= hour < 20:
        # 暮：从午过渡到夜，17点=0.5, 20点=0.95
        return 0.50 + (hour - 17) / 3.0 * 0.45
    else:
        # 夜：深褐暖，0点到5点最深
        if hour >= 20:
            night_progress = (hour - 20) / 4.0
        else:
            night_progress = (hour + 4) / 9.0  # 0h→0.44, 5h→1.0
        return 0.80 + min(night_progress, 1.0) * 0.15


def lerp_hex_colors(hex_a: str, hex_b: str, t: float) -> str:
    """线性插值两个十六进制颜色，返回 #RRGGBB。"""
    t = max(0.0, min(1.0, t))
    ra = int(hex_a[1:3], 16); ga = int(hex_a[3:5], 16); ba = int(hex_a[5:7], 16)
    rb = int(hex_b[1:3], 16); gb = int(hex_b[3:5], 16); bb = int(hex_b[5:7], 16)
    r = int(ra + (rb - ra) * t)
    g = int(ga + (gb - ga) * t)
    b = int(ba + (bb - ba) * t)
    return f"#{r:02X}{g:02X}{b:02X}"


def get_daynight_bg_color() -> str:
    """
    根据当前真实时间，返回叠加了昼夜色调的画布基础色。
    """
    period = get_day_period()
    factor = _get_daynight_tint_factor()
    base = BG_YELLOW_1
    if period == "dawn":
        target = DAYNIGHT_DAWN_COLOR
    elif period == "dusk":
        target = DAYNIGHT_DUSK_COLOR
    elif period == "night":
        target = DAYNIGHT_NIGHT_COLOR
    else:
        target = DAYNIGHT_NOON_COLOR
    # factor 控制 target 混合强度：factor=0 纯 base, factor=1 纯 target
    # 实际只用微妙混合：最多 8% 的色调偏移
    blend_strength = factor * 0.08  # 最大 8% 偏移，非常克制
    return lerp_hex_colors(base, target, blend_strength)
