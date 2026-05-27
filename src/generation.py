"""
Génération : LLM via Azure OpenAI ou HuggingFace local.
"""
from __future__ import annotations

import time
from functools import lru_cache

from src.config import (
    AZURE_API_VERSION,
    AZURE_ENDPOINT,
    DEVICE,
    GenerationConfig,
    SYSTEM_PROMPT,
    azure_available,
    get_azure_api_key,
    resolve_chat_deployments,
)


class BaseGenerator:
    cfg: GenerationConfig

    def generate(self, system: str, user: str) -> str:
        raise NotImplementedError


class AzureGenerator(BaseGenerator):
    def __init__(self, cfg: GenerationConfig):
        from openai import AzureOpenAI

        if not azure_available():
            raise RuntimeError("Azure non configuré")
        self.cfg = cfg
        self.api_key = get_azure_api_key()
        self.client = AzureOpenAI(
            azure_endpoint=AZURE_ENDPOINT,
            api_key=self.api_key,
            api_version=AZURE_API_VERSION,
        )

    def generate(self, system: str, user: str) -> str:
        deployments = resolve_chat_deployments(self.cfg.model_id)
        last_error = None
        for deployment in deployments:
            for attempt in range(3):
                try:
                    resp = self.client.chat.completions.create(
                        model=deployment,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        temperature=self.cfg.temperature,
                        max_tokens=self.cfg.max_tokens,
                        seed=self.cfg.seed,
                    )
                    return resp.choices[0].message.content or ""
                except Exception as e:
                    last_error = e
                    if attempt == 2:
                        break
                    time.sleep(2 ** attempt)
        if last_error is not None:
            raise last_error
        return ""


class HFGenerator(BaseGenerator):
    """LLM HuggingFace local (avec quantification 4-bit si bitsandbytes dispo)."""
    def __init__(self, cfg: GenerationConfig):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch

        self.cfg = cfg
        self.tokenizer = AutoTokenizer.from_pretrained(cfg.model_id, trust_remote_code=True)
        kwargs = {"trust_remote_code": True}
        try:
            import bitsandbytes  # noqa
            from transformers import BitsAndBytesConfig
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
            )
            kwargs["device_map"] = "auto"
        except ImportError:
            kwargs["torch_dtype"] = torch.float16 if DEVICE.startswith("cuda") else torch.float32
            kwargs["device_map"] = "auto" if DEVICE.startswith("cuda") else None
        self.model = AutoModelForCausalLM.from_pretrained(cfg.model_id, **kwargs)

    def generate(self, system: str, user: str) -> str:
        import torch
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        try:
            prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        except Exception:
            prompt = f"{system}\n\n{user}\n"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=self.cfg.max_tokens,
                do_sample=self.cfg.temperature > 0,
                temperature=max(self.cfg.temperature, 1e-5),
                pad_token_id=self.tokenizer.eos_token_id,
            )
        text = self.tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return text.strip()


@lru_cache(maxsize=2)
def get_generator(cfg_name: str) -> BaseGenerator:
    from src.config import GENERATION_CONFIGS
    cfg = next((c for c in GENERATION_CONFIGS if c.name == cfg_name), None)
    if cfg is None:
        raise ValueError(f"Generator inconnu: {cfg_name}")
    if cfg.provider == "azure":
        return AzureGenerator(cfg)
    return HFGenerator(cfg)


def format_context(retrieved) -> str:
    """Formate les chunks récupérés en contexte numéroté pour le prompt."""
    parts = []
    for i, r in enumerate(retrieved, 1):
        meta = r.chunk.metadata.get("filename", r.chunk.doc_id)
        parts.append(f"[{i}] (source: {meta})\n{r.chunk.text.strip()}")
    return "\n\n".join(parts)


def answer_question(question: str, retrieved, gen_cfg_name: str) -> str:
    gen = get_generator(gen_cfg_name)
    context = format_context(retrieved)
    user = SYSTEM_PROMPT.format(context=context, question=question)
    return gen.generate(system="Tu réponds en français sauf si la question est en anglais.", user=user)
