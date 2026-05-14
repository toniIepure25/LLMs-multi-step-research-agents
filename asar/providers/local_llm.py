"""
Local SLM provider — implements `LLMClientProtocol` using `transformers`.

This is the inference-time wrapper for the SLM that the rest of ASAR sees as
an `LLMClientProtocol`. It can load either:

- a base model only (e.g. ``Qwen/Qwen2.5-0.5B-Instruct``), or
- a base model + a LoRA adapter directory produced by
  ``scripts/finetune_lora.py``.

The provider is intentionally minimal: load model + tokenizer once, do a
single-turn chat-template generation per request, return the same
``LLMGenerationResponse`` shape that the OpenAI adapter returns.

Hardware:
- Apple Silicon: uses MPS automatically when available
- CPU: falls back to ``cpu`` device
- CUDA: uses ``cuda`` when available
"""

from __future__ import annotations

import os
from typing import Any

from asar.core.errors import ConfigurationError, LLMClientError
from asar.core.llm import LLMGenerationRequest, LLMGenerationResponse, TokenUsage


_DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


class LocalSLMClient:
    """Local transformers-backed SLM client.

    Construction is lazy — model weights are loaded only on the first
    ``generate`` call. This keeps test imports cheap and avoids paying
    multi-second model-load times until they are actually needed.
    """

    def __init__(
        self,
        *,
        base_model: str | None = None,
        adapter_path: str | None = None,
        device: str | None = None,
        dtype: str = "float32",
        max_new_tokens_cap: int = 512,
    ) -> None:
        self._base_model = base_model or os.environ.get("ASAR_LOCAL_BASE_MODEL") or _DEFAULT_BASE_MODEL
        self._adapter_path = adapter_path or os.environ.get("ASAR_LOCAL_ADAPTER_PATH") or None
        self._device_override = device or os.environ.get("ASAR_LOCAL_DEVICE")
        self._dtype = dtype
        self._max_new_tokens_cap = max_new_tokens_cap
        self._model = None
        self._tokenizer = None
        self._device = None

    # -- public API ------------------------------------------------------

    @property
    def adapter_path(self) -> str | None:
        return self._adapter_path

    @property
    def base_model(self) -> str:
        return self._base_model

    async def generate(self, request: LLMGenerationRequest) -> LLMGenerationResponse:
        try:
            self._lazy_load()
        except ImportError as exc:  # pragma: no cover - optional dep
            raise ConfigurationError(
                "Local SLM provider requires `transformers`. Run `uv sync --extra local-llm`.",
                details={"error": str(exc)},
            ) from exc
        except Exception as exc:
            raise LLMClientError(
                "Local SLM provider failed to load model",
                details={
                    "base_model": self._base_model,
                    "adapter_path": self._adapter_path,
                    "error": str(exc),
                },
            ) from exc

        try:
            output_text, usage = self._generate_sync(request)
        except Exception as exc:
            raise LLMClientError(
                "Local SLM generation failed",
                details={
                    "model": request.model,
                    "metadata": request.metadata,
                    "error": str(exc),
                },
            ) from exc

        return LLMGenerationResponse(
            model=f"{self._base_model}+adapter:{self._adapter_path}" if self._adapter_path else self._base_model,
            output_text=output_text,
            finish_reason="stop",
            usage=usage,
            raw_response={
                "base_model": self._base_model,
                "adapter_path": self._adapter_path,
                "device": str(self._device),
            },
        )

    # -- internals -------------------------------------------------------

    def _lazy_load(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return

        import torch  # type: ignore
        from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore

        self._device = self._resolve_device(torch)
        torch_dtype = self._resolve_dtype(torch)

        tokenizer = AutoTokenizer.from_pretrained(self._base_model, use_fast=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self._base_model,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
        )

        if self._adapter_path:
            try:
                from peft import PeftModel  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise ConfigurationError(
                    "Local SLM provider with an adapter requires `peft`. "
                    "Run `uv sync --extra local-llm`.",
                ) from exc
            model = PeftModel.from_pretrained(model, self._adapter_path)

        model.to(self._device)
        model.eval()

        self._tokenizer = tokenizer
        self._model = model

    def _resolve_device(self, torch: Any) -> str:
        if self._device_override:
            return self._device_override
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _resolve_dtype(self, torch: Any) -> Any:
        if self._dtype == "float16":
            return torch.float16
        if self._dtype == "bfloat16":
            return torch.bfloat16
        return torch.float32

    def _generate_sync(self, request: LLMGenerationRequest) -> tuple[str, TokenUsage]:
        assert self._tokenizer is not None and self._model is not None
        import torch  # type: ignore

        chat = [
            {"role": msg.role.value, "content": msg.content}
            for msg in request.messages
        ]
        prompt = self._tokenizer.apply_chat_template(
            chat, tokenize=False, add_generation_prompt=True
        )
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._device)
        input_token_count = int(inputs["input_ids"].shape[1])

        max_new_tokens = min(self._max_new_tokens_cap, request.max_tokens)
        with torch.no_grad():
            generation = self._model.generate(
                **inputs,
                do_sample=request.temperature > 0,
                temperature=max(request.temperature, 1e-5),
                top_p=0.95,
                max_new_tokens=max_new_tokens,
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
            )
        new_tokens = generation[0, inputs["input_ids"].shape[1] :]
        text = self._tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
        if not text:
            raise LLMClientError(
                "Local SLM returned empty output",
                details={"model": self._base_model, "prompt_chars": len(prompt)},
            )
        usage = TokenUsage(
            input_tokens=input_token_count,
            output_tokens=int(new_tokens.shape[0]),
        )
        return text, usage


def build_local_llm_client(
    *,
    base_model: str | None = None,
    adapter_path: str | None = None,
) -> LocalSLMClient:
    """Factory wrapper used by the live provider builder."""
    return LocalSLMClient(base_model=base_model, adapter_path=adapter_path)
