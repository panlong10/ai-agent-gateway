import json
import httpx
from typing import Optional

from app.database import LLMConfig


class LLMService:
    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider
        self.api_key = config.api_key
        self.model = config.model
        self.base_url = config.base_url

    async def parse_intent(self, query: str, available_intents: list[dict]) -> dict:
        available_intents_str = json.dumps(available_intents, ensure_ascii=False)

        system_prompt = f"""你是一个意图解析器。根据用户的自然语言输入，确定用户想要执行的意图。

可用的意图列表：
{available_intents_str}

请根据用户输入确定意图并提取参数。
返回 JSON 格式：
{{
    "intent_name": "意图名称",
    "params": {{参数字典}}
}}

如果无法确定意图，返回：
{{
    "intent_name": null,
    "params": {{}}
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        response = await self._chat(messages)

        try:
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {"intent_name": None, "params": {}}

    async def _chat(self, messages: list[dict]) -> str:
        if self.provider == "openai":
            return await self._openai_chat(messages)
        elif self.provider == "anthropic":
            return await self._anthropic_chat(messages)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _openai_chat(self, messages: list[dict]) -> str:
        base = self.base_url or "https://api.openai.com"

        if "openrouter" in base:
            url = "https://openrouter.ai/api/v1/chat/completions"
        else:
            url = base.rstrip("/") + "/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if "openrouter" in self.base_url:
            headers["HTTP-Referer"] = "https://ai-agent-gateway"
            headers["X-Title"] = "AI Agent Gateway"

        payload = {"model": self.model, "messages": messages, "temperature": 0.1}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise ValueError(f"LLM API error: {e.response.text}")
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""

    async def _anthropic_chat(self, messages: list[dict]) -> str:
        url = (self.base_url or "https://api.anthropic.com") + "/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        system = messages[0]["content"] if messages[0]["role"] == "system" else None
        user_messages = [m for m in messages if m["role"] == "user"]
        last_user_msg = user_messages[-1]["content"] if user_messages else ""

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": last_user_msg}],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]


async def create_llm_service(config: LLMConfig) -> LLMService:
    return LLMService(config)
