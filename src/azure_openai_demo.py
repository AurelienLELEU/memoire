"""
Single-file Azure OpenAI demo.

This script is fully self-contained: all Azure settings are defined below.
You can copy this file into an empty folder and run it directly.
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
from typing import Iterable, Optional

# ======== Hardcoded Azure configuration ========
# Chat deployment (gpt35turbo)
CHAT_ENDPOINT = "https://labtp-openai.openai.azure.com/"
CHAT_API_VERSION = "2024-12-01-preview"
CHAT_DEPLOYMENT = "gpt35turbo"
CHAT_DEPLOYMENT_FALLBACKS = ("gpt35turbo", "gpt-35-turbo")

# Embedding deployment (ada-002)
EMB_ENDPOINT = "https://labtp-openai.openai.azure.com/"
EMB_API_VERSION = "2024-06-01"
EMB_DEPLOYMENT = "ada-002"
EMB_DEPLOYMENT_FALLBACKS = ("ada-002", "text-embedding-ada-002")

# Azure Key Vault defaults
KEY_VAULT_URL = "https://kv-databricks-labtp.vault.azure.net"
KEY_VAULT_SECRET_NAME = "labopenaikey"


def get_azure_openai_class():
    try:
        module = importlib.import_module("openai")
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])  # nosec B603
        module = importlib.import_module("openai")
    return getattr(module, "AzureOpenAI")


def get_secret_client_class():
    try:
        module = importlib.import_module("azure.keyvault.secrets")
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "azure-keyvault-secrets"]
        )  # nosec B603
        module = importlib.import_module("azure.keyvault.secrets")
    return getattr(module, "SecretClient")


def get_default_credential_class():
    try:
        module = importlib.import_module("azure.identity")
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "azure-identity"]
        )  # nosec B603
        module = importlib.import_module("azure.identity")
    return getattr(module, "DefaultAzureCredential")


def get_api_key(
    explicit_env_name: Optional[str] = None,
    key_vault_url: str = KEY_VAULT_URL,
    key_vault_secret_name: str = KEY_VAULT_SECRET_NAME,
) -> str:
    if explicit_env_name:
        value = os.getenv(explicit_env_name)
        if value:
            return value
        raise RuntimeError(
            f"Environment variable '{explicit_env_name}' is empty or undefined"
        )

    # Primary path: Azure Key Vault
    try:
        SecretClient = get_secret_client_class()
        DefaultAzureCredential = get_default_credential_class()
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=key_vault_url, credential=credential)
        secret = client.get_secret(key_vault_secret_name)
        if secret.value:
            return secret.value
    except Exception as exc:
        raise RuntimeError(
            "Unable to read API key from Azure Key Vault. "
            "Ensure Azure auth is configured (for example: az login) and that you can access "
            f"{key_vault_url} / secret '{key_vault_secret_name}'. Details: {exc}"
        ) from exc

    candidates: Iterable[str] = (
        "CHAT_OPENAI_KEY",
        "OPENAI_KEY",
        "AZURE_OPENAI_API_KEY",
        "EMB_OPENAI_KEY",
    )
    for name in candidates:
        value = os.getenv(name)
        if value:
            return value

    raise RuntimeError(
        "No Azure OpenAI API key available. "
        "Set one of: CHAT_OPENAI_KEY, OPENAI_KEY, AZURE_OPENAI_API_KEY, EMB_OPENAI_KEY"
    )


def run_chat(
    endpoint: str,
    api_version: str,
    deployment: str,
    api_key: str,
    prompt: str,
    max_tokens: int,
) -> str:
    AzureOpenAI = get_azure_openai_class()
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    deployments = [deployment] + [d for d in CHAT_DEPLOYMENT_FALLBACKS if d != deployment]
    last_error: Optional[Exception] = None
    for candidate in deployments:
        try:
            response = client.chat.completions.create(
                model=candidate,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            return content if content else ""
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    return ""


def run_embedding(
    endpoint: str,
    api_version: str,
    deployment: str,
    api_key: str,
    text: str,
) -> list[float]:
    AzureOpenAI = get_azure_openai_class()
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
    )

    deployments = [deployment] + [d for d in EMB_DEPLOYMENT_FALLBACKS if d != deployment]
    last_error: Optional[Exception] = None
    for candidate in deployments:
        try:
            response = client.embeddings.create(
                model=candidate,
                input=text,
            )
            return response.data[0].embedding
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    return []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test Azure OpenAI chat (gpt35turbo) and embeddings (ada-002)."
    )
    parser.add_argument(
        "--api-key-env",
        type=str,
        default=None,
        help="Name of the environment variable containing the Azure OpenAI API key",
    )
    parser.add_argument(
        "--key-vault-url",
        type=str,
        default=KEY_VAULT_URL,
        help="Azure Key Vault URL",
    )
    parser.add_argument(
        "--key-vault-secret",
        type=str,
        default=KEY_VAULT_SECRET_NAME,
        help="Secret name in Azure Key Vault that contains Azure OpenAI API key",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="Donne-moi un resume de Azure OpenAI en 2 phrases.",
        help="Prompt sent to gpt35turbo",
    )
    parser.add_argument(
        "--embed-text",
        type=str,
        default="Texte de test pour creer un embedding.",
        help="Input text for ada-002",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=250,
        help="Max tokens for chat completion",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        api_key = get_api_key(
            explicit_env_name=args.api_key_env,
            key_vault_url=args.key_vault_url,
            key_vault_secret_name=args.key_vault_secret,
        )

        chat_output = run_chat(
            endpoint=CHAT_ENDPOINT,
            api_version=CHAT_API_VERSION,
            deployment=CHAT_DEPLOYMENT,
            api_key=api_key,
            prompt=args.prompt,
            max_tokens=args.max_tokens,
        )

        embedding = run_embedding(
            endpoint=EMB_ENDPOINT,
            api_version=EMB_API_VERSION,
            deployment=EMB_DEPLOYMENT,
            api_key=api_key,
            text=args.embed_text,
        )

        print("=== Azure OpenAI connectivity test ===")
        print(f"Chat deployment: {CHAT_DEPLOYMENT}")
        print(f"Embedding deployment: {EMB_DEPLOYMENT}")
        print("\n--- Chat response ---")
        print(chat_output)
        print("\n--- Embedding info ---")
        print(f"Vector size: {len(embedding)}")
        print(f"First 8 values: {[round(v, 6) for v in embedding[:8]]}")

        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
