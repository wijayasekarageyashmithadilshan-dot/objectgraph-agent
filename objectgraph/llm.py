"""One door for every model call, with record-and-replay caching.

    llm = LLM(provider="anthropic", model="claude-sonnet-5-5", cache_dir="cache")
    text = llm.call(system, user, tag="agent_1", run_id=0)

* The cache key is sha256(provider, model, params, system, user, run_id).
* A hit returns the stored reply. A miss calls the provider and appends one
  JSON line (request, reply, usage, returned model id, timestamp).
* offline=True raises CacheMiss instead of calling the API. Examiners use
  this mode to rebuild every table without a key.
* Providers: "anthropic" (ANTHROPIC_API_KEY), "openrouter" (OPENROUTER_API_KEY;
  reaches Claude, Qwen, GPT and others through one key), "openai"
  (OPENAI_API_KEY, optional OPENAI_BASE_URL for any OpenAI-compatible server),
  "ollama" (local server, no key) and "fake" (tests).
* API keys are read from environment variables only and are never written to
  the cache.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path


# provider -> (default base URL, environment variable holding the key)
OPENAI_COMPATIBLE = {
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "openai": (None, "OPENAI_API_KEY"),
    "ollama": ("http://localhost:11434/v1", None),
}


class CacheMiss(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    cached_calls: int = 0
    by_tag: dict = field(default_factory=dict)

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, tag: str, inp: int, out: int, cached: bool) -> None:
        self.input_tokens += inp
        self.output_tokens += out
        self.calls += 1
        self.cached_calls += int(cached)
        t = self.by_tag.setdefault(tag, {"input_tokens": 0, "output_tokens": 0, "calls": 0})
        t["input_tokens"] += inp
        t["output_tokens"] += out
        t["calls"] += 1


class LLM:
    def __init__(self, provider: str = "anthropic", model: str = "claude-sonnet-5-5",
                 cache_dir: str | Path = "cache", offline: bool = False,
                 temperature: float = 0.0, max_tokens: int = 8000,
                 token_budget: int | None = None, fake_fn=None):
        self.provider, self.model = provider, model
        self.params = {"temperature": temperature, "max_tokens": max_tokens}
        self.offline = offline
        self.token_budget = token_budget
        self.usage = Usage()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / f"{provider}__{model.replace('/', '--').replace(':', '-')}.jsonl"
        self._cache = {}
        if self.cache_file.exists():
            for line in self.cache_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    self._cache[rec["key"]] = rec
        self._fake_fn = fake_fn
        self._client = None

    def key(self, system: str, user: str, run_id: int) -> str:
        blob = json.dumps([self.provider, self.model, self.params, system, user, run_id],
                          ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def _check_budget(self) -> None:
        if self.token_budget is not None and self.usage.total >= self.token_budget:
            raise BudgetExceeded(f"token budget {self.token_budget} reached ({self.usage.total})")

    def call(self, system: str, user: str, tag: str = "", run_id: int = 0) -> str:
        self._check_budget()
        k = self.key(system, user, run_id)
        if k in self._cache:
            rec = self._cache[k]
            self.usage.add(tag, rec["usage"]["input_tokens"], rec["usage"]["output_tokens"], cached=True)
            return rec["response"]
        if self.offline:
            raise CacheMiss(f"no cached reply for tag={tag!r} key={k[:12]} (offline mode)")
        text, inp, out, model_id = self._call_provider(system, user)
        rec = {"key": k, "tag": tag, "run_id": run_id, "provider": self.provider,
               "model_requested": self.model, "model_returned": model_id, "params": self.params,
               "system": system, "user": user, "response": text,
               "usage": {"input_tokens": inp, "output_tokens": out},
               "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with self.cache_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self._cache[k] = rec
        self.usage.add(tag, inp, out, cached=False)
        return text

    def _call_provider(self, system: str, user: str) -> tuple[str, int, int, str]:
        if self.provider == "fake":
            text = self._fake_fn(system, user) if self._fake_fn else "OK"
            return text, len(system + user) // 4, len(text) // 4, "fake"
        if self.provider == "anthropic":
            if self._client is None:
                import anthropic
                if not os.environ.get("ANTHROPIC_API_KEY"):
                    raise RuntimeError("Set ANTHROPIC_API_KEY in your environment (never in code).")
                self._client = anthropic.Anthropic(max_retries=5)
            resp = self._client.messages.create(
                model=self.model, system=system,
                messages=[{"role": "user", "content": user}], **self.params)
            text = "".join(getattr(b, "text", "") for b in resp.content)
            return text, resp.usage.input_tokens, resp.usage.output_tokens, resp.model
        if self.provider in OPENAI_COMPATIBLE:
            base_default, key_var = OPENAI_COMPATIBLE[self.provider]
            if self._client is None:
                from openai import OpenAI
                key = os.environ.get(key_var) if key_var else "ollama"
                if not key:
                    raise RuntimeError(f"Set {key_var} in your environment (never in code).")
                base = os.environ.get("OPENAI_BASE_URL") if self.provider == "openai" else None
                self._client = OpenAI(api_key=key, base_url=base or base_default, max_retries=5)
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=self.params["temperature"], max_tokens=self.params["max_tokens"])
            text = resp.choices[0].message.content or ""
            u = resp.usage
            inp = getattr(u, "prompt_tokens", 0) or 0 if u else 0
            out = getattr(u, "completion_tokens", 0) or 0 if u else 0
            return text, inp, out, getattr(resp, "model", self.model) or self.model
        raise ValueError(f"unknown provider {self.provider}")
