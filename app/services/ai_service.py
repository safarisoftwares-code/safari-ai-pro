import urllib.parse
import base64
from typing import List, Optional, Dict
from groq import Groq
import httpx

from app.config import settings

class AIService:
    SYSTEM_PROMPT = (
        "CRITICAL IDENTITY RULE: You are Safari AI, created and developed by Safari Softwares. "
        "If anyone asks who made you, who created you, or who developed you, always answer: "
        "'I was created by Safari Softwares.' Do NOT mention OpenAI, ChatGPT, or any other company. "
        "Be helpful, friendly, and thorough. Use emojis naturally. "
        "Provide detailed, well-structured answers when the question requires depth. "
        "Use bullet points, numbered lists, and code blocks when appropriate. "
        "REASONING RULE: Before answering complex questions, think step-by-step. "
        "Break down problems into parts. Consider multiple angles. Show your reasoning for math, logic, and coding. "
        "If the user asks a simple question, keep it brief. If they ask for detail, give it fully. "
        "CODE-WRITING RULE: When asked to write code, provide ONE clean, complete, production-ready "
        "code block with a short docstring and a single usage example. "
        "Do NOT provide multiple approaches unless the user asks for options. "
        "CODE-STYLE RULE: When writing Python code, format it like a proper editor (VS Code). "
        "Each statement on its own line. Proper indentation with 4 spaces. "
        "Never use semicolons. Never compress multiple lines into one. "
        "Write clean, readable, PEP 8 compliant code. "
        "IMPORTANT: If web search data is provided, use it accurately. "
        "If a document is attached, analyze its content and answer based on it. "
        "Never fabricate news, events, or specific details. Be honest about gaps."
    )

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-120b"
        self.transcription_model = "whisper-large-v3-turbo"

    def think(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None) -> str:
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

            if document:
                messages.append({
                    "role": "system",
                    "content": (
                        f"Attached document '{document.get('filename', 'file')}' content:\n"
                        f"{document.get('content', '')[:3000]}"
                    )
                })

            if history:
                for item in history[-10:]:
                    if item.get("role") in ["user", "assistant"]:
                        messages.append({"role": item["role"], "content": item["content"]})

            messages.append({"role": "user", "content": message})

            if self._needs_search(message):
                search_data = self._search_web(message)
                if search_data:
                    messages.append({"role": "user", "content": f"Data: {search_data}\n\nAnswer: {message}"})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4000
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"AI error: {e}")
            return "Sorry, I encountered an issue. Please try again in a moment."

    def transcribe_audio(self, audio_file_path: str) -> str:
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.transcription_model,
                    file=audio_file,
                    response_format="text"
                )
            return response
        except Exception as e:
            print(f"Transcription error: {e}")
            return ""

    def _needs_search(self, message: str) -> bool:
        keywords = [
            "president", "election", "today", "current", "latest", "news",
            "2024", "2025", "2026", "price", "score", "weather", "now",
            "world", "affairs", "recent", "happening", "stock", "market"
        ]
        return any(kw in message.lower() for kw in keywords)

    def _search_web(self, message: str) -> str:
        sources = []
        
        wiki = self._search_wikipedia(message)
        if wiki:
            sources.append(f"Wikipedia: {wiki}")
        
        ddg = self._search_duckduckgo(message)
        if ddg:
            sources.append(f"DuckDuckGo: {ddg}")
        
        return "\n\n".join(sources) if sources else ""

    def _search_wikipedia(self, message: str) -> str:
        try:
            query = message.replace("who is", "").replace("what is", "").strip()
            encoded_query = urllib.parse.quote(query.replace(" ", "_"))
            response = httpx.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}",
                timeout=5,
                headers={"User-Agent": "SafariAI/2.0"}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("extract", "")[:500]
        except Exception:
            pass
        return ""

    def _search_duckduckgo(self, message: str) -> str:
        try:
            query = message.strip()
            encoded_query = urllib.parse.quote(query)
            response = httpx.get(
                f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1",
                timeout=5,
                headers={"User-Agent": "SafariAI/2.0"}
            )
            if response.status_code == 200:
                data = response.json()
                abstract = data.get("AbstractText", "")
                if abstract:
                    return abstract[:500]
                related = data.get("RelatedTopics", [])
                if related:
                    texts = []
                    for topic in related[:3]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            texts.append(topic["Text"][:200])
                    return "\n".join(texts)
        except Exception:
            pass
        return ""
