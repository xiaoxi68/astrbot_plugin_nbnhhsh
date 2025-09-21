from __future__ import annotations

import re

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, register

from .cache import TTLCache
from .client import NbnhhshClient
from .service import NbnhhshResult, NbnhhshService

NBNHHSH_API_URL = "https://lab.magiconch.com/api/nbnhhsh/"
DEFAULT_TIMEOUT = 10.0
DEFAULT_CACHE_TTL = 3600
DEFAULT_CACHE_MAX_SIZE = 1024


@register(
    "nbnhhsh",
    "qingzhixing & contributors",
    "神奇海螺缩写查询插件",
    "0.1.0",
    "https://github.com/qingzhixing/nonebot-plugin-nbnhhsh-q",
)
class NbnhhshPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self._pattern = re.compile(
            r"(?P<keyword>[a-zA-Z0-9]{2,})(?:是什么|是啥|是什么意思)[?？]?",
            re.IGNORECASE,
        )
        self._client = NbnhhshClient(base_url=NBNHHSH_API_URL, timeout=DEFAULT_TIMEOUT)
        self._service = NbnhhshService(
            client=self._client,
            cache=TTLCache(ttl_seconds=DEFAULT_CACHE_TTL, max_size=DEFAULT_CACHE_MAX_SIZE),
            logger=logger,
        )

    async def initialize(self):
        await self._client.startup()
        logger.info("nbnhhsh plugin initialised")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_shorthand_query(self, event: AstrMessageEvent):
        if not self._mentioned_bot(event):
            return

        message = (event.message_str or "").strip()
        if not message:
            return

        match = self._pattern.fullmatch(message)
        if not match:
            return

        keyword = match.group("keyword")
        logger.info("nbnhhsh received keyword: %s", keyword)

        result = await self._service.lookup(keyword)
        event.should_call_llm(False)

        if result and result.translations:
            yield event.plain_result(self._build_reply(result))
        else:
            yield event.plain_result(self._not_found_reply(keyword))

    @filter.command_group("nbnhhsh")
    def nbnhhsh_group(self):
        """nbnhhsh 管理指令"""
        pass

    @nbnhhsh_group.command("clear_cache")
    async def clear_cache(self, event: AstrMessageEvent):
        """清理 nbnhhsh 查询缓存"""
        self._service.clear_cache()
        event.should_call_llm(False)
        yield event.plain_result("nbnhhsh 缓存已清理")

    async def terminate(self):
        await self._client.shutdown()
        logger.info("nbnhhsh plugin terminated")

    @staticmethod
    def _build_reply(result: NbnhhshResult) -> str:
        translations = result.translations
        if len(translations) == 1:
            body = translations[0]
        else:
            head = "，".join(translations[:-1]) if len(translations) > 1 else ""
            tail = translations[-1]
            body = f"{head}，或者 {tail}" if head else tail
        return f"{result.keyword} 可能是: {body}"

    @staticmethod
    def _not_found_reply(keyword: str) -> str:
        return f"没能找到 {keyword} 的含义"

    @staticmethod
    def _mentioned_bot(event: AstrMessageEvent) -> bool:
        message_obj = getattr(event, "message_obj", None)
        if not message_obj:
            return False

        self_id = str(event.get_self_id() or "")
        for component in getattr(message_obj, "message", []) or []:
            if isinstance(component, Comp.At) and str(getattr(component, "qq", "")) == self_id:
                return True
        return False
