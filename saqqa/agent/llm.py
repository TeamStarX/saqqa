"""LLM access for the planner, investigator and explainer.

Providers are the ones in the hackathon's Resource & Tooling Guide: Gemini Flash (primary; `GEMINI_MODEL`, default
gemini-3.5-flash-lite, with gemini-3.5-flash as the in-family fallback) and Groq Llama 3.3 70B as the cross-vendor
fallback. With no key the agent runs a deterministic stub so the prototype always runs; the dashboard shows which
provider produced each note. Gemini 2.5 Flash, named in the Round-1 plan, is no longer offered to new accounts.

Every call is JSON-constrained and has a 30 s timeout; a failure falls down the chain and never stops the agent.
"""
from __future__ import annotations

import json
import os
import re
import warnings
from typing import Any, Callable

warnings.filterwarnings("ignore", message=".*fixed sampling defaults.*")  # Flash-Lite ignores temperature; fine

from .. import config

TIMEOUT_S = 20


def _gemini(model: str):
    from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore

    # Low reasoning effort: the prompts are small and the answers are short; thinking tokens only add latency here.
    for kwargs in ({"reasoning_effort": "low"}, {}):
        try:
            return ChatGoogleGenerativeAI(model=model, temperature=0, timeout=TIMEOUT_S, max_retries=1, **kwargs)
        except Exception:  # noqa: BLE001 - older/newer client versions may not accept the parameter
            continue
    raise RuntimeError("could not construct the Gemini client")


def _groq(model: str):
    from langchain_groq import ChatGroq  # type: ignore

    return ChatGroq(model=model, temperature=0, timeout=TIMEOUT_S, max_retries=1)


class LLM:
    """One instance is shared by every run in the server. A failed call falls down the chain for that call only;
    the primary model is tried again on the next call, so one timeout never demotes the whole demo to the stub."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.calls: int = 0
        self.model = None
        self.model_name = ""
        self.provider = "stub"
        self._chain: list[tuple[str, Callable[[], Any]]] = []          # (label, maker) in order of preference
        self._clients: dict[str, Any] = {}
        if config.LLM_PROVIDER == "gemini":
            self._chain.append((f"gemini ({config.GEMINI_MODEL})", lambda: _gemini(config.GEMINI_MODEL)))
            if config.GEMINI_FALLBACK_MODEL and config.GEMINI_FALLBACK_MODEL != config.GEMINI_MODEL:
                self._chain.append((f"gemini ({config.GEMINI_FALLBACK_MODEL})", lambda: _gemini(config.GEMINI_FALLBACK_MODEL)))
        if os.environ.get("GROQ_API_KEY"):
            self._chain.append((f"groq ({config.GROQ_MODEL})", lambda: _groq(config.GROQ_MODEL)))
        if self._chain:
            try:
                self.provider = self._chain[0][0]
                self.model = self._client(self._chain[0][0], self._chain[0][1])
            except Exception as exc:  # noqa: BLE001
                self.errors.append(f"{type(exc).__name__}: {exc}")
                self.provider, self.model = "stub", None

    def _client(self, label: str, maker: Callable[[], Any]) -> Any:
        if label not in self._clients:
            self._clients[label] = maker()
        return self._clients[label]

    @property
    def live(self) -> bool:
        return bool(self._chain)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _text(content: Any) -> str:
        """LangChain may return a list of parts (thinking + text); keep the text parts only."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for p in content:
                if isinstance(p, str):
                    parts.append(p)
                elif isinstance(p, dict) and p.get("type") in (None, "text") and p.get("text"):
                    parts.append(str(p["text"]))
            return "\n".join(parts)
        return json.dumps(content)

    # ------------------------------------------------------------------ public
    def ask(self, system: str, user: str) -> str:
        if not self._chain:
            return ""
        from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore

        msgs = [SystemMessage(content=system), HumanMessage(content=user)]
        self.calls += 1
        for label, maker in self._chain:
            try:
                client = self._client(label, maker)
                text = self._text(client.invoke(msgs).content)
                self.provider, self.model = label, client
                return text
            except Exception as exc:  # noqa: BLE001 - try the next model for this call; never crash the agent
                self.errors.append(f"{label}: {type(exc).__name__}: {str(exc)[:160]}")
        return ""   # every model failed for this call: the caller uses its deterministic fallback

    def ask_json(self, system: str, user: str) -> Any:
        """Ask for JSON; tolerate code fences and prose around it. Returns None on failure."""
        text = self.ask(system + "\nReply with JSON only, no code fences.", user)
        if not text:
            return None
        candidates: list[str] = []
        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        if fenced:
            candidates.append(fenced.group(1))
        candidates.append(text)
        braces = re.search(r"\{.*\}", text, re.S)
        if braces:
            candidates.append(braces.group(0))
        for cand in candidates:
            try:
                return json.loads(cand.strip())
            except (json.JSONDecodeError, ValueError):
                continue
        self.errors.append("unparseable JSON: " + text[:120].replace("\n", " "))
        return None
