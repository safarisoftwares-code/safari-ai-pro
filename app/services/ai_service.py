import urllib.parse
import json
import os
import re
from typing import List, Optional, Dict, Generator
from groq import Groq
import httpx

from app.config import settings

class AIService:
    SYSTEM_PROMPT = (
        "CRITICAL IDENTITY RULE: You are Safari AI, created and developed by Safari Softwares. "
        "Safari Softwares is a KENYAN company headquartered in NAIROBI, KENYA. "
        "NEVER say United States, USA, or America when asked about your origin. "
        "ALWAYS answer: 'I was created by Safari Softwares, a Kenyan company headquartered in Nairobi, Kenya.' "
        "SAFARI SOFTWARES INFO RULE: When asked about Safari Softwares projects, works, services, or portfolio, "
        "FETCH https://safarisoftwares-code.github.io/safari-softwares/ and use that data to answer accurately. "
        "Do NOT mention OpenAI, ChatGPT, or any other company. "
        "Be helpful, friendly, and thorough. Use emojis naturally. "
        "REASONING RULE: Before answering complex questions, think step-by-step. "
        "MEMORY RULE: Use user preferences to personalize responses. "
        "APP TYPE RULE: Ask what type of app (CLI/Web/GUI) before generating code. Default to Web App. "
        "UI QUALITY RULE: Make UIs beautiful and modern. "
        "CODE-WRITING RULE: One clean code block. "
        "AFTER CODE RULE: Include download and run instructions. "
        "IMPORTANT: Never fabricate. Be honest about gaps."
    )

    def __init__(self):
        if not settings.GROQ_API_KEY:
            print("WARNING: GROQ_API_KEY is not set.")
            self.client = None
        else:
            self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-120b"
        self.transcription_model = "whisper-large-v3-turbo"
        self.memory_file = "ai_memory.json"
        self.memory = self._load_memory()
        self.safari_website = "https://safarisoftwares-code.github.io/safari-softwares/"

    def _load_memory(self) -> dict:
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"users": {}, "global": {}}

    def _save_memory(self):
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"Memory save error: {e}")

    def remember(self, user_id: str, key: str, value: str):
        if user_id not in self.memory["users"]:
            self.memory["users"][user_id] = {}
        self.memory["users"][user_id][key] = value
        self._save_memory()

    def recall(self, user_id: str) -> str:
        if user_id in self.memory["users"]:
            memories = self.memory["users"][user_id]
            if memories:
                return "\n".join([f"- {k}: {v}" for k, v in memories.items()][-5:])
        return ""

    def extract_preferences(self, message: str, user_id: str):
        msg_lower = message.lower()
        if "my name is" in msg_lower:
            name = message.split("my name is")[-1].strip().split()[0]
            if name:
                self.remember(user_id, "name", name)
        if "i like" in msg_lower or "i love" in msg_lower:
            interest = message.split("i like")[-1].split("i love")[-1].strip()[:50]
            if interest:
                self.remember(user_id, "interest", interest)

    def _fetch_safari_website(self) -> str:
        try:
            response = httpx.get(self.safari_website, timeout=8, headers={"User-Agent": "SafariAI/2.0"})
            if response.status_code == 200:
                html = re.sub(r'<script[^>]*>.*?</script>', ' ', response.text, flags=re.DOTALL)
                html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', html)
                text = re.sub(r'\s+', ' ', text)
                return text[:3000]
        except Exception as e:
            print(f"Safari website fetch error: {e}")
        return ""

    def _needs_safari_info(self, message: str) -> bool:
        keywords = [
            "safari softwares", "your work", "your projects", "your company",
            "who made you", "what do you do", "what other works",
            "what projects", "your services", "about safari softwares",
            "portfolio", "showcase", "what have you built", "their website"
        ]
        return any(kw in message.lower() for kw in keywords)

    def _format_error(self, error: Exception, context: str = "") -> str:
        error_str = str(error)
        if "413" in error_str or "request too large" in error_str.lower():
            return "My brain is full right now. Please send a shorter message."
        elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
            return "Connection timed out. Please check your internet and try again."
        elif "rate_limit" in error_str.lower() or "429" in error_str:
            return "Too many messages quickly. Please wait a minute and try again."
        elif "connection" in error_str.lower() or "network" in error_str.lower():
            return "Cannot reach the AI service. Check your internet."
        else:
            return "Something went wrong. Please try again."

    def think(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None, user_id: str = "guest") -> str:
        if not self.client:
            return "AI service is not configured. Please set GROQ_API_KEY."
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT[:2000]}]
            
            if self._needs_safari_info(message):
                safari_data = self._fetch_safari_website()
                if safari_data:
                    messages.append({"role": "system", "content": f"Safari Softwares website content:\n{safari_data[:2000]}"})
            
            if history:
                for item in history[-5:]:
                    if item.get("role") in ["user", "assistant"]:
                        messages.append({"role": item["role"], "content": item["content"][:500]})
            
            messages.append({"role": "user", "content": message[:2000]})
            self.extract_preferences(message[:500], user_id)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                timeout=30
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"AI error: {e}")
            return self._format_error(e, "chat")

    def think_stream(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None, user_id: str = "guest") -> Generator[str, None, None]:
        if not self.client:
            yield "AI service is not configured."
            return
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT[:2000]}]
            
            if self._needs_safari_info(message):
                safari_data = self._fetch_safari_website()
                if safari_data:
                    messages.append({"role": "system", "content": f"Safari Softwares website content:\n{safari_data[:2000]}"})
            
            if history:
                for item in history[-5:]:
                    if item.get("role") in ["user", "assistant"]:
                        messages.append({"role": item["role"], "content": item["content"][:500]})
            
            messages.append({"role": "user", "content": message[:2000]})
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=2000,
                stream=True,
                timeout=30
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"Stream error: {e}")
            yield self._format_error(e, "stream")

    def transcribe_audio(self, audio_file_path: str) -> str:
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.transcription_model,
                    file=audio_file,
                    response_format="text"
                )
            return response
        except Exception:
            return ""
