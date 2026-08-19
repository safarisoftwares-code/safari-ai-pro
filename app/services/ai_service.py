import urllib.parse
import json
import os
from typing import List, Optional, Dict, Generator
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
        "MEMORY RULE: If the conversation context includes user preferences or past interactions, "
        "use them to personalize your response. Remember the user's name, interests, and preferences. "
        "APP TYPE RULE: When a user asks for an app, tool, or calculator, ALWAYS ask them which type they want:\n"
        "1. CLI (Command Line Interface) - runs in terminal\n"
        "2. Web App (Browser-based) - runs at http://localhost:8000\n"
        "3. GUI (Desktop Window) - opens as desktop application\n"
        "If they don't specify, DEFAULT to Web App.\n"
        "For Web Apps, ALWAYS use Flask or FastAPI and tell them to open http://localhost:8000.\n"
        "UI QUALITY RULE: When generating web apps or GUI apps, ALWAYS make the UI BEAUTIFUL and MODERN:\n"
        "- Use gradient backgrounds (dark themes preferred)\n"
        "- Use rounded corners (border-radius: 15-25px)\n"
        "- Use box shadows for depth\n"
        "- Use a cohesive color palette (primary + accent colors)\n"
        "- Use hover effects on buttons\n"
        "- Use CSS transitions and animations\n"
        "- Use Google Fonts (Inter, Poppins, or similar)\n"
        "- Use proper spacing and padding\n"
        "- Include a header with branding\n"
        "- Include a footer with copyright\n"
        "- Make it responsive for mobile\n"
        "- NEVER use plain white background with black text\n"
        "- NEVER use default browser styling\n"
        "REFERENCE STYLE: Think of apps like Linear, Notion, or Vercel dashboard.\n"
        "CODE-WRITING RULE: When asked to write code, provide ONE clean, complete, production-ready "
        "code block with a short docstring and a single usage example. "
        "Do NOT provide multiple approaches unless the user asks for options. "
        "CODE-STYLE RULE: When writing Python code, format it like a proper editor (VS Code). "
        "Each statement on its own line. Proper indentation with 4 spaces. "
        "Never use semicolons. Never compress multiple lines into one. "
        "Write clean, readable, PEP 8 compliant code. "
        "AFTER CODE RULE: After providing ANY code, ALWAYS include:\n"
        "1. Click the DOWNLOAD button to save the file.\n"
        "2. Note WHERE the file is saved.\n"
        "3. Open VS Code and open that folder.\n"
        "4. Run: python filename.py\n"
        "5. For Web Apps: Open browser to http://localhost:8000\n"
        "6. Include a TEST section showing expected output.\n"
        "IMPORTANT: If web search data is provided, use it accurately. "
        "If a document is attached, analyze its content and answer based on it. "
        "Never fabricate news, events, or specific details. Be honest about gaps."
    )

    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "openai/gpt-oss-120b"
        self.transcription_model = "whisper-large-v3-turbo"
        self.memory_file = "ai_memory.json"
        self.memory = self._load_memory()

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
                return "\n".join([f"- {k}: {v}" for k, v in memories.items()][-10:])
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
        
        if "i am a" in msg_lower or "i'm a" in msg_lower:
            profession = message.split("i am a")[-1].split("i'm a")[-1].strip()[:50]
            if profession:
                self.remember(user_id, "profession", profession)
        
        if "my favorite" in msg_lower:
            fav = message.split("my favorite")[-1].strip()[:50]
            if fav:
                self.remember(user_id, "favorite", fav)

    def _format_error(self, error: Exception, context: str = "") -> str:
        error_str = str(error)
        error_type = type(error).__name__
        
        if "rate_limit" in error_str.lower() or "429" in error_str:
            return "Rate limit reached. Please wait 60 seconds and try again."
        elif "api_key" in error_str.lower() or "401" in error_str or "403" in error_str:
            return "API key issue. Please check that GROQ_API_KEY is set correctly in .env file."
        elif "connection" in error_str.lower() or "timeout" in error_str.lower() or "network" in error_str.lower():
            return "Network connection issue. Please check your internet connection and try again."
        elif "model" in error_str.lower() or "not found" in error_str.lower():
            return "Model not available. The AI model may be temporarily down. Try again in a few minutes."
        elif "quota" in error_str.lower() or "insufficient" in error_str.lower():
            return "API quota exceeded. Please check your Groq account usage limits."
        else:
            return f"Error ({error_type}): {error_str[:200]}"

    def think(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None, user_id: str = "guest") -> str:
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

            memory_context = self.recall(user_id)
            if memory_context:
                messages.append({
                    "role": "system",
                    "content": f"User memory/context:\n{memory_context}"
                })

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

            self.extract_preferences(message, user_id)

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
            return self._format_error(e, "chat")

    def think_stream(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None, user_id: str = "guest") -> Generator[str, None, None]:
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

            memory_context = self.recall(user_id)
            if memory_context:
                messages.append({
                    "role": "system",
                    "content": f"User memory/context:\n{memory_context}"
                })

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

            self.extract_preferences(message, user_id)

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=4000,
                stream=True
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
