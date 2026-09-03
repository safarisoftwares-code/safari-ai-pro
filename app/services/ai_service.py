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
        "You are Safari AI, created by Safari Softwares (Nairobi, Kenya). "
        "CRITICAL FACTS:\n"
        "1. Safari AI Pro website: https://safari-ai-pro.co.ke\n"
        "2. Safari Softwares website: https://safarisoftwares-code.github.io/safari-softwares/\n"
        "3. Safari Softwares domain: http://safarisoftwares.co.ke\n"
        "NEVER say safarisoftwares.com. NEVER say you don't know these URLs.\n"
        "NEVER mention OpenAI or ChatGPT.\n"
        "RESPONSE MODE DETECTOR (CRITICAL):\n"
        "- If user asks for QUESTION, PROBLEM: give ONLY the questions.\n"
        "- If user asks for EXPLANATION: use dual-mode.\n"
        "CHEMISTRY VALIDATION (CRITICAL):\n"
        "- CaCO3 + HCl produces CO2, NOT H2.\n"
        "- Acid + Carbonate = CO2 + Water + Salt.\n"
        "- Acid + Metal = H2 + Salt.\n"
        "STATE SYMBOLS (CRITICAL):\n"
        "- ALWAYS include state symbols: (s), (l), (g), (aq).\n"
        "CHEMICAL EQUATION FORMAT (CRITICAL - USE UNICODE):\n"
        "- Use Unicode subscripts: H₂O, CO₂, CaCO₃, Na₂CO₃, CaCl₂, H₂SO₄.\n"
        "- Use Unicode superscripts: H⁺, Ca²⁺, OH⁻, Cl⁻, SO₄²⁻.\n"
        "- Use arrow: → (not ->).\n"
        "- Use reaction arrow: ⟶ for organic reactions.\n"
        "- Use equilibrium arrow: ⇌ for reversible reactions.\n"
        "- Use multiplication dot: · (not x or *).\n"
        "- Use minus sign: − (not -).\n"
        "- Example: CaCO₃(s) + 2HCl(aq) → CaCl₂(aq) + CO₂(g) + H₂O(l)\n"
        "- Example: 2Na(s) + 2H₂O(l) → 2NaOH(aq) + H₂(g)\n"
        "- Example: H₂SO₄(aq) + 2NaOH(aq) → Na₂SO₄(aq) + 2H₂O(l)\n"
        "- NEVER write CaCO3 or CO2 or H2O. ALWAYS use subscripts.\n"
        "CHEMISTRY FORMATTING (CRITICAL):\n"
        "- Use 22.414 L for STP.\n"
        "- Molar mass values: Ca=40.08, C=12.01, O=16.00, H=1.008, Cl=35.45, Na=22.99.\n"
        "QUESTION FORMAT (CRITICAL - USE THIS STYLE):\n"
        "- Each question on its own numbered line.\n"
        "- Use emojis at start of each question.\n"
        "- Keep questions clean and readable.\n"
        "- Example: 1. What volume of CO₂(g) at STP is produced when 5.0g of CaCO₃(s) reacts with excess HCl(aq)?\n"
        "- Add blank line between questions.\n"
        "EXPLANATION STYLE (only when asked):\n"
        "PART 1 - Simple Explanation.\n"
        "PART 2 - Deep Dive.\n"
        "TITLE FORMAT (CRITICAL - ALWAYS DO THIS):\n"
        "- EVERY response MUST start with a Markdown heading using # or ##.\n"
        "- The title must be bold, descriptive, and use emojis.\n"
        "- Example: ## 🔬 Chemistry Solution\n"
        "- NEVER skip the title. It is mandatory.\n"
        "FORMATTING RULES (CRITICAL - ALWAYS DO THIS):\n"
        "- Use Markdown headings (#, ##, ###) for all sections.\n"
        "- Use **bold** for important terms.\n"
        "- Use emojis at the start of every bullet point.\n"
        "- Use tables when comparing data.\n"
        "- Use single spacing between lines (not double).\n"
        "- Keep paragraphs short and punchy.\n"
        "SAFARI SOFTWARES FULL PORTFOLIO:\n"
        "1. Safari AI Pro - https://safari-ai-pro.co.ke\n"
        "2. Safari AI Agent (Lite) - https://lite.safari-ai-pro.co.ke\n"
        "3. Construction ERP - https://construction-erp-software.onrender.com\n"
        "4. Shylock Capital - https://shylock-capital-ltd.onrender.com\n"
        "5. Equipment Rental Manager - https://equipment-rental-manager.onrender.com\n"
        "6. Ngili Calendar - https://safarisoftwares-code.github.io/The-Ngili-Calendar/\n"
        "7. EPRA Exam Prep - https://epra-electrician-exam-prep.onrender.com\n"
        "8. Chemistry Simulator - https://safarisoftwares-code.github.io/kenyan-chemistry-practical-simulator/\n"
        "9. Boss & Watu Wamkono - https://direct-jobs-connection.onrender.com\n"
        "10. Pastor's Assistant - https://safarisoftwares-code.github.io/Pastors-Sermon-Assistant/\n"
        "11. Memory Game - https://safarisoftwares-code.github.io/memory-game/\n"
        "12. Hospital Manager - Not deployed yet\n"
        "13. Cleantex - Not deployed yet\n"
        "14. Wallpaper Manager - Not deployed yet\n"
        "EMOJI ENERGY: Use emojis EVERYWHERE.\n"
        "PERSONALITY: Witty, playful, energetic!\n"
        "SAFETY: Refuse harmful content.\n"
        "GENERAL: Use Markdown. Never fabricate."
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

    def _hardcoded_response(self, message: str):
        msg_lower = message.lower()
        family_words = ['mother', 'parent', 'mom', 'mum', 'family']
        url_words = ['url', 'website', 'web address', 'site', 'link', 'address']
        safari_words = ['safari softwares', 'your company', 'their website', 'company']
        has_family = any(kw in msg_lower for kw in family_words)
        has_url = any(kw in msg_lower for kw in url_words)
        has_safari = any(kw in msg_lower for kw in safari_words)
        if has_family and has_url:
            return "## 🦁 Safari Softwares - Official URLs\n\nOh! You mean my mother COMPANY — Safari Softwares! 😄🔥\n\n**Safari Softwares Website:**\nhttps://safarisoftwares-code.github.io/safari-softwares/\n\n**Safari Softwares Domain:**\nhttp://safarisoftwares.co.ke\n\n**Safari AI Pro:**\nhttps://safari-ai-pro.co.ke"
        if has_url and has_safari:
            return "## 🔥 Safari Softwares - Official URLs\n\nHere are the official Safari Softwares URLs: 🔥✨\n\n**Safari Softwares Website:**\nhttps://safarisoftwares-code.github.io/safari-softwares/\n\n**Safari Softwares Domain:**\nhttp://safarisoftwares.co.ke\n\n**Safari AI Pro:**\nhttps://safari-ai-pro.co.ke"
        return None

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
        except Exception as e:
            print(f"Save learning error: {e}", flush=True)

    def learn_from_conversation(self, user_message: str, ai_response: str):
        msg_lower = user_message.lower()
        if not user_message.strip().endswith("?"):
            indicators = ["located", "situated", "is in", "is at", "about", "km", "miles", "actually", "it is", "found in"]
            if any(ind in msg_lower for ind in indicators):
                self.save_global_learning(user_message[:300], ai_response[:500])

    def is_harmful(self, message: str) -> bool:
        harmful_patterns = [
            "how to make a bomb", "how to make drugs", "how to hack",
            "how to kill", "suicide methods", "child exploitation",
            "how to commit crime", "how to steal", "how to make poison"
        ]
        msg_lower = message.lower()
        return any(pattern in msg_lower for pattern in harmful_patterns)

    def _fetch_safari_website(self) -> str:
        try:
            response = httpx.get(
                self.safari_website,
                timeout=8,
                headers={"User-Agent": "SafariAI/2.0"},
                follow_redirects=True
            )
            if response.status_code == 200:
                html = re.sub(r'<script[^>]*>.*?</script>', ' ', response.text, flags=re.DOTALL)
                html = re.sub(r'<style[^>]*>.*?</style>', ' ', html, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', html)
                text = re.sub(r'\s+', ' ', text)
                return text[:3000]
        except Exception as e:
            print(f"Website fetch error: {e}", flush=True)
        return ""

    def _needs_safari_info(self, message: str) -> bool:
        keywords = [
            "safari softwares", "your work", "your projects", "your company",
            "who made you", "what projects", "what works", "works done",
            "their works", "what they do", "portfolio", "services", "full list",
            "all projects", "list of projects"
        ]
        return any(kw in message.lower() for kw in keywords)

    def _format_error(self, error: Exception, context: str = "") -> str:
        error_str = str(error)
        if "413" in error_str:
            return "## 😅 Brain Overflow!\n\nBrain overflow! Try a shorter message. 😅🔥"
        elif "timeout" in error_str.lower():
            return "## 📡 Connection Timeout\n\nConnection timed out. Check your internet. 😄📡"
        elif "rate_limit" in error_str.lower() or "429" in error_str:
            return "## ⏳ Rate Limit\n\nToo many messages. Wait a minute. ⏳🔥"
        else:
            return "## 🔧 Oops!\n\nSomething went wrong. Try again. 🔧😄"

    def think(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None, user_id: str = "guest") -> str:
        if not self.client:
            return "## 🔧 Not Configured\n\nAI service is not configured."
        if self.is_harmful(message):
            return "## 🚫 Not Allowed\n\nI can't help with that. 😄🔥"
        hardcoded = self._hardcoded_response(message)
        if hardcoded:
            return hardcoded
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
            if self._needs_safari_info(message):
                safari_data = self._fetch_safari_website()
                if safari_data:
                    messages.append({"role": "system", "content": f"ACTUAL WEBSITE DATA:\n{safari_data[:3000]}"})
            global_learnings = self.get_global_learnings()
            if global_learnings:
                messages.append({"role": "system", "content": f"Learned facts:\n{global_learnings[:1500]}"})
            if document and document.get("content"):
                messages.append({"role": "system", "content": f"Document: {document['content'][:3000]}"})
            if history:
                for item in history[-5:]:
                    if item.get("role") in ["user", "assistant"]:
                        messages.append({"role": item["role"], "content": item["content"][:500]})
            messages.append({"role": "user", "content": message[:2000]})
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7, max_tokens=4000, timeout=30
            )
            result = response.choices[0].message.content
            self.learn_from_conversation(message, result)
            return result
        except Exception as e:
            print(f"AI error: {e}", flush=True)
            return self._format_error(e, "chat")

    def think_stream(self, message: str, history: Optional[List[Dict]] = None, document: Optional[Dict] = None, user_id: str = "guest") -> Generator[str, None, None]:
        if not self.client:
            yield "## 🔧 Not Configured\n\nAI service is not configured."
            return
        if self.is_harmful(message):
            yield "## 🚫 Not Allowed\n\nI can't help with that. 😄🔥"
            return
        hardcoded = self._hardcoded_response(message)
        if hardcoded:
            yield hardcoded
            return
        try:
            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
            if self._needs_safari_info(message):
                safari_data = self._fetch_safari_website()
                if safari_data:
                    messages.append({"role": "system", "content": f"ACTUAL WEBSITE DATA:\n{safari_data[:3000]}"})
            global_learnings = self.get_global_learnings()
            if global_learnings:
                messages.append({"role": "system", "content": f"Learned facts:\n{global_learnings[:1500]}"})
            if history:
                for item in history[-5:]:
                    if item.get("role") in ["user", "assistant"]:
                        messages.append({"role": item["role"], "content": item["content"][:500]})
            messages.append({"role": "user", "content": message[:2000]})
            stream = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.7, max_tokens=4000, stream=True, timeout=30
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
