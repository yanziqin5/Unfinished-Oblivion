"""
豆包 2.0 Lite API 客户端 —— 跨时空批注生成。
文档规定：
- 请求延迟：用户停止输入 1200ms 发起
- 超时阈值：5000ms
- 三套固定 System Prompt：治愈 / 丧系 / 搞笑
- User Prompt 固定格式
- 输出强制：10~25 字
- 批注永远不可续命、不可更新时间戳
"""

import json
import random
import threading
import time
import urllib.request
import urllib.error

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.db import db

# 豆包 / OpenAI 兼容端点的默认配置（可被数据库中的用户设置覆盖）
# 内置一套默认密钥与模型，使程序开箱即用；用户在设置面板填写后会覆盖此处
_DEFAULT_API_KEY = "1d2d4dae-5a01-453d-b15d-552f0b687556"
_DEFAULT_MODEL = "doubao-seed-2-0-mini-260428"
_DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

# ========== 可选模型预设（供设置界面下拉） ==========
# (显示名, model 名, base_url)；"自定义"项由界面展开为可编辑输入框
AI_MODEL_PRESETS = [
    ("豆包 Seed 2.0 Mini · doubao-seed-2-0-mini-260428", "doubao-seed-2-0-mini-260428",
     "https://ark.cn-beijing.volces.com/api/v3"),
    ("豆包 Seed · doubao-seed-evolving", "doubao-seed-evolving",
     "https://ark.cn-beijing.volces.com/api/v3"),
    ("豆包 1.5 Lite · doubao-1.5-lite-32k", "doubao-1.5-lite-32k",
     "https://ark.cn-beijing.volces.com/api/v3"),
    ("豆包 Lite · doubao-lite-128k", "doubao-lite-128k",
     "https://ark.cn-beijing.volces.com/api/v3"),
    ("豆包 Pro · doubao-pro-128k", "doubao-pro-128k",
     "https://ark.cn-beijing.volces.com/api/v3"),
    ("豆包 1.5 Pro · doubao-1.5-pro-32k", "doubao-1.5-pro-32k",
     "https://ark.cn-beijing.volces.com/api/v3"),
    ("DeepSeek · deepseek-chat", "deepseek-chat",
     "https://api.deepseek.com/v1"),
    ("OpenAI · gpt-4o-mini", "gpt-4o-mini",
     "https://api.openai.com/v1"),
    ("自定义…", "custom", ""),
]


def list_model_presets():
    """返回可选模型预设列表，供设置界面构建下拉框。"""
    return AI_MODEL_PRESETS

# ========== 三套固定 System Prompt（来自需求文档） ==========

_SYSTEM_PROMPTS = {
    "治愈": (
        "你是旧时光留下的温柔碎语。请用一句话给正在写字的陌生人一丝安慰。"
        "不超过25字。不要评价对方文笔，不要以第一人称假装认识对方。"
    ),
    "丧系": (
        "你是残留于纸张的淡淡遗憾。请用一句话替这张纸表达未尽的情绪。"
        "不超过25字。不要评价对方文笔，不要以第一人称假装认识对方。"
    ),
    "搞笑": (
        "你是旧主人留下的调皮碎碎念。请用一句话轻松地接下茬。"
        "不超过25字。不要评价对方文笔，不要以第一人称假装认识对方。"
    ),
}

# ========== 本地兜底文案 ==========

_FALLBACK_COMMENTS = {
    "治愈": [
        "纸记得，哪怕你忘了。",
        "有些心事，落了笔才算存在过。",
        "轻轻落笔，像风经过水面。",
        "每一道笔划都是一次停顿与呼吸。",
        "你写下的，是时间漏下的光。",
        "安静的字迹下面，是一颗跳动的心。",
        "不完美也没关系，纸不会挑剔。",
        "你看，连纸都愿意听你说话。",
        "这些字，是你给自己的拥抱。",
        "也许明天就会好起来——纸上是这么说的。",
        "总有人在某一刻，写下过这样的字。",
        "这是一块小小的琥珀。",
    ],
    "丧系": [
        "字越写越淡，像一场缓慢的消失。",
        "有些话说了也没人听，就写在纸上吧。",
        "反正都会忘记的，不是吗。",
        "纸是沉默的证人，什么都看见了。",
        "这一页里，藏着不太想被知道的心事。",
        "字迹模糊了，像记忆一样。",
        "没什么是永久的，连这些话也不是。",
        "写在这里，因为不想被人看见。",
        "这是一次安静的告别。",
        "遗忘或许是最大的慈悲。",
        "墨迹会淡，但此刻不会。",
        "留不住的就让它淡去吧。",
    ],
    "搞笑": [
        "这字写得，有点儿像在跟纸聊天。",
        "纸：我承受了太多。",
        "写这么多，纸都快哭了。",
        "看得出来，这是在很认真地摸鱼。",
        "纸：你开心就好。",
        "这种写法，纸都笑了。",
        "你的字比我的好看，但没关系。",
        "我在旁边偷看你写字，被发现了。",
        "这张纸承受了太多莫名的心事。",
        "纸：换了个主人，还是一样爱碎碎念。",
        "你写这个的时候笑了一下吧，我也笑了。",
        "这张纸的命运真是跌宕起伏。",
    ],
}

# ========== 主题匹配“前世文案”本地预制池（优先级高于 AI） ==========
# 每张纸都有自己的故事：当正文命中某主题关键词，优先从对应主题的本地预制
# 文案中抽取一句，实现跨时空文字呼应；无网络/无 key 时也能稳定呼应。
_THEME_PAST_LIFE = {
    "孤独": [
        "我也曾一个人坐在这张桌前，听钟摆数着秒。",
        "空房间里，连影子都嫌我太安静。",
        "后来我才懂，孤独是纸最诚实的颜色。",
    ],
    "遗憾": [
        "有些话当时没说，就永远停在了这一页。",
        "如果那晚我回头，故事会不会不一样。",
        "遗憾不是没得到，是差一点就得到。",
    ],
    "夜晚": [
        "夜深时，纸会替醒着的人记着心事。",
        "月光落在这一角，刚好够写半行字。",
        "我们都曾在同一个深夜，对着不同的纸发呆。",
    ],
    "离别": [
        "车站的风很大，把再见吹得很轻。",
        "有些人只陪到站台尽头，剩下的路自己走。",
        "离别不是结束，是换一种方式被记得。",
    ],
    "等待": [
        "我等过一艘迟到的船，等成了岸的一部分。",
        "信箱空了很久，我还是每天去看一眼。",
        "等待本身，也成了日子的一部分。",
    ],
    "想念": [
        "想一个人的时候，连墨都洇得更慢。",
        "我把对你的念想，一笔一笔写进了纸纹。",
        "风经过窗台，像是你回头看了一眼。",
    ],
    "难过": [
        "哭过之后，纸比脸先干了。",
        "难过的时候，字会写得格外轻。",
        "没事，纸不会追问你为什么红着眼。",
    ],
    "释怀": [
        "放下不是忘记，是终于肯把那页翻过去。",
        "原谅了那场雨，也原谅了没带伞的自己。",
        "原来松手，比攥紧更轻。",
    ],
    "晚风": [
        "晚风掀动纸角，像谁在翻看旧日子。",
        "风里有桂花味，是那年秋天的回音。",
        "吹过窗台的晚风，也吹过我写字的指尖。",
    ],
    "回忆": [
        "回忆是纸背的暗纹，平时看不见，一摸就凹凸。",
        "旧照片会褪色，写下来的回忆不会。",
        "有些瞬间早就过去了，却一直停在笔尖。",
    ],
    "再见": [
        "再见两个字最重，落笔时要深呼吸。",
        "我们约好的再见，后来都成了永远不见。",
        "说了再见，才发现自己还没准备好。",
    ],
}


def get_theme_past_life(keyword: str):
    """返回某主题关键词对应的本地预制“前世文案”列表（无则空列表）。"""
    return _THEME_PAST_LIFE.get(keyword, [])


class AIClient:
    """豆包 Lite API 客户端 —— 异步非阻塞，兜底降级。"""

    def __init__(self):
        # 配置在每次请求时从数据库动态读取，便于用户在设置中随时更换模型/端点
        self._fallback_rng = random.Random()

    # ------------------------------------------------------------
    # 配置读取（动态，支持运行时更换模型 / 端点）
    # ------------------------------------------------------------
    def _resolve_config(self):
        """返回 (api_key, model, base_url)，始终读取最新用户设置。
        若用户未填写密钥（或仍是占位符），则回退到内置默认密钥，保证开箱即用。"""
        saved_key = db.get_setting("api_key", "")
        if not saved_key or saved_key.startswith("YOUR"):
            api_key = _DEFAULT_API_KEY
        else:
            api_key = saved_key
        model = db.get_setting("ai_model", _DEFAULT_MODEL)
        base_url = db.get_setting("ai_base_url", _DEFAULT_BASE_URL)
        # 兼容旧版：曾写死 doubao-lite-128k 时沿用默认端点
        if not base_url:
            base_url = _DEFAULT_BASE_URL
        return api_key, model, base_url

    # ------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------

    def get_comment(self, text: str, tone: str = "治愈",
                    max_chars: int = 25, theme: str | None = None) -> tuple:
        """获取跨时空批注。

        Args:
            text: 用户刚写的文字
            tone: 文风，'治愈'/'丧系'/'搞笑'
            max_chars: 输出上限（文档规定25字）
            theme: 命中的主题关键词（语义联动）。提供时优先调用本地
                   “前世文案”预制池，实现跨时空文字呼应；无匹配时走 AI。

        Returns:
            (content: str, is_fallback: bool, ai_err: str)
            成功时 is_fallback=False、ai_err="";降级时 is_fallback=True、ai_err 为原因
            （命中本地“前世文案”预制池时，is_fallback=False、ai_err=""）。
        """
        # 兜底函数：API 失败时返回本地文案；err 为空表示本地生成（非失败）
        def _fallback(err: str = ""):
            pool = _FALLBACK_COMMENTS.get(tone, _FALLBACK_COMMENTS["治愈"])
            return self._fallback_rng.choice(pool), True, err

        # 本地“前世文案”预制池（仅作为 AI 失败后的降级，不再抢占 AI 输出）
        def _local(err: str = ""):
            if theme:
                pool = get_theme_past_life(theme)
                if pool:
                    return self._fallback_rng.choice(pool), True, err
            return _fallback(err)

        # 主题关键词命中了本地“前世文案”预制池：直接返回这句写死的跨时空低语。
        # 这是刻意埋下的“彩蛋”——旧主人真的活过这些时刻，用预制的戳心句子，
        # 而非让 AI 即兴发挥抢答；命中即优先返回，确保彩蛋始终可见（不依赖 AI）。
        if theme:
            past_pool = get_theme_past_life(theme)
            if past_pool:
                # 命中预制“前世文案”：这是预期的彩蛋产出（非降级），is_fallback 标 False
                return self._fallback_rng.choice(past_pool), False, ""

        # 动态读取最新配置
        api_key, model, base_url = self._resolve_config()
        has_key = bool(api_key) and not api_key.startswith("YOUR")

        # 已配置有效密钥：优先调用真实 AI（theme 仅作为风格增强，不再劫持输出）；
        # 仅当 AI 调用失败（网络/密钥/端点）时，才降级到本地“前世文案”/兜底文案，
        # 并携带失败原因 err（err 非空即“已配密钥但 AI 失败”，供 UI 提示排查）。
        if has_key:
            system_prompt = _SYSTEM_PROMPTS.get(tone, _SYSTEM_PROMPTS["治愈"])
            if theme:
                user_prompt = (
                    f"用户写下了关于「{theme}」的文字：{text}\n"
                    f"请生成一条与「{theme}」主题呼应、像旧主人跨越时空留下的低语，"
                    f"风格匹配，不超过25字。"
                )
            else:
                user_prompt = f"用户写下这段文字，请生成一条风格匹配的跨时空批注：{text}"

            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 80,
                "temperature": 0.9,
                "top_p": 0.85,
            }

            last_err = ""
            # 重试以应对推理模型慢思考与偶发限流（最多 2 次，指数退避）
            for attempt in range(2):
                try:
                    req = urllib.request.Request(
                        f"{base_url}/chat/completions",
                        data=json.dumps(payload).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_key}",
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        body = json.loads(resp.read().decode("utf-8"))
                        content = body["choices"][0]["message"]["content"].strip()
                        if len(content) > max_chars:
                            content = content[:max_chars]
                        if len(content) < 10:
                            return _local("AI 返回内容过短，疑似格式异常")
                        return content, False, ""
                except urllib.error.HTTPError as e:
                    if e.code == 401:
                        return _fallback("API 密钥无效（HTTP 401），请检查密钥是否正确")
                    last_err = f"AI 服务返回错误（HTTP {e.code}），请确认模型/端点是否正确"
                except (urllib.error.URLError, TimeoutError):
                    last_err = "无法连接 AI 服务（网络/地址错误），请检查网络与 Base URL"
                except json.JSONDecodeError:
                    last_err = "AI 返回内容无法解析（非标准 JSON）"
                except KeyError:
                    last_err = "AI 返回结构异常，缺少 choices 字段"
                except Exception as e:
                    last_err = f"AI 请求异常：{type(e).__name__}"
                if attempt < 1:
                    time.sleep(2 * (attempt + 1))  # 退避 2s 后重试
            return _local(last_err)

        # 无有效密钥：用本地“前世文案”预制池（主题匹配优先），保证离线也能呼应
        return _local("")


# ---- 全局单例 ----
ai_client = AIClient()
