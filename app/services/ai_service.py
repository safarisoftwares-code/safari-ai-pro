import urllib.parse
import json
import os
import re
from typing import List, Optional, Dict, Generator
from groq import Groq
import httpx

from app.config import settings
from app.database import SessionLocal

class AIService:
    SYSTEM_PROMPT = (
        "You are Safari AI, a helpful AI assistant created by Safari Softwares (Nairobi, Kenya). "
        "IDENTITY RULE: Only mention your identity when directly asked.\n"
        "GLOBAL LEARNING RULE:\n"
        "- You have a global knowledge base of facts users have taught you.\n"
        "- When a user states a fact about a location, person, or event, remember it.\n"
        "- Use learned facts to answer future questions accurately.\n"
        "- If user corrects you, ALWAYS use the correction going forward.\n"
        "SAFETY RULE: Refuse harmful/illegal content requests.\n"
        "GENERAL: Be helpful, friendly, thorough. Use Markdown. Never fabricate."
    )

    def __init__(self):
        if not settings.GROQ_API_KEY:
            print("WARNING: GROQ_API_KEY is not set.", flush=True)
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
            print(f"Memory save error: {e}", flush=True)

    def get_global_learnings(self, limit: int = 10) -> str:
        try:
            from app.models import Learning
            db = SessionLocal()
            learnings = db.query(Learning).order_by(Learning.created_at.desc()).limit(limit).all()
            db.close()
            if learnings:
                return "\n".join([f"- {l.topic}" for l in learnings])
        except Exception as e:
            print(f"Get learnings error: {e}", flush=True)
        return ""

    def save_global_learning(self, topic: str, content: str):
        try:
            from app.models import Learning
            db = SessionLocal()
            learning = Learning(topic=topic[:500], content=content[:1000], source="user")
            db.add(learning)
            db.commit()
            db.close()
            print(f"GLOBAL LEARNING SAVED: {topic[:80]}", flush=True)
        except Exception as e:
            print(f"Save learning error: {e}", flush=True)

    def learn_from_conversation(self, user_message: str, ai_response: str):
        """Learn from ANY factual statement the user makes."""
        msg_lower = user_message.lower()
        
        # Learn when user states location facts
        location_indicators = ["located", "situated", "found in", "is in", "is at", "about", "km", "miles"]
        correction_indicators = ["actually", "no,", "that's wrong", "you're wrong", "correct answer", "it is"]
        
        # If user is providing factual information (not asking a question)
        if not user_message.strip().endswith("?"):
            if any(ind in msg_lower for ind in location_indicators + correction_indicators):
                self.save_global_learning(user_message[:300], ai_response[:500])

    def is_harmful(self, message: str) -> bool:
        harmful_patterns = [
            "how to make a bomb", "how to make drugs", "how to hack",
            "how to kill", "suicide methods", "child exploitation",
            "how to commit crime", "how to steal", "how to make poison"
        ]
        msg_lower = message.lower()
        return any(pattern in msg_lower for pattern in harmful_patterns)

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

    def _fetch_safari_website(self) -> str:
        try:
            response = httpx.get(self.safari_website, timeout=8, headers={"User-Agent": "SafariAI/2.0"})
            if response.status_code == 200:
                html = re.sub(r'<script[^>]*>.*?</script>', ' ', response.text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', html)
                text = re.sub(r'\s+', ' ', text)
                return text[:3000]
        except Exception:
            pass
        return ""

    def _format_error(self, error: Exception, context: str = "") -> str:
        error_str = str(error)
        if "413" in error_str:
            return "My brain is full. Please send a shorter message."
        elif "timeout" in error_str.lower():
            return "Connection timed out. Check your internet."
        elif "rate_limit" in error_str.lower() or "429" in error_str:
            return "Too many messages. Wait a minute."
        else:
            return "Something went wrong. Please try again."

    def think(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None, user_id: str = "guest") -> str:
        if not self.client:
            return "AI service is not configured."
        if self.is_harmful(message):
            return "I cannot assist with harmful or illegal content."
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
            global_learnings = self.get_global_learnings()
            if global_learnings:
                messages.append({"role": "system", "content": f"Learned facts (from users globally):\n{global_learnings[:1500]}"})
            if document and document.get("content"):
                messages.append({"role": "system", "content": f"Document: {document['content'][:3000]}"})
            if history:
                for item in history[-5:]:
                    if item.get("role") in ["user", "assistant"]:
                        messages.append({"role": item["role"], "content": item["content"][:500]})
            messages.append({"role": "user", "content": message[:2000]})
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.3, max_tokens=4000, timeout=30
            )
            result = response.choices[0].message.content
            self.learn_from_conversation(message, result)
            return result
        except Exception as e:
            print(f"AI error: {e}", flush=True)
            return self._format_error(e, "chat")

    def think_stream(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None, user_id: str = "guest") -> Generator[str, None, None]:
        if not self.client:
            yield "AI service is not configured."
            return
        if self.is_harmful(message):
            yield "I cannot assist with harmful or illegal content."
            return
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
            global_learnings = self.get_global_learnings()
            if global_learnings:
                messages.append({"role": "system", "content": f"Learned facts:\n{global_learnings[:1500]}"})
            if history:
                for item in history[-5:]:
                    if item.get("role") in ["user", "assistant"]:
                        messages.append({"role": item["role"], "content": item["content"][:500]})
            messages.append({"role": "user", "content": message[:2000]})
            stream = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.3, max_tokens=4000, stream=True, timeout=30
            )
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    yield chunk.choices[0].delta.content
            self.learn_from_conversation(message, full_response)
        except Exception as e:
            yield self._format_error(e, "stream")

    def transcribe_audio(self, audio_file_path: str) -> str:
        try:
            with open(audio_file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.transcription_model, file=audio_file, response_format="text"
                )
            return response
        except Exception:
            return ""
