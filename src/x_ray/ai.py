"""AI-related functions for analyzing MongoDB log lines."""

import logging
import os
from openai import OpenAI
from x_ray.utils import green, ai_key

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
MAX_NEW_TOKENS = 256
GPT_MODEL = "gpt-4o-mini"  # Use gpt-4o-mini for faster and cheaper responses

logger = logging.getLogger(__name__)


def detect_device():
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    except ImportError:
        logger.error("torch is not installed. Please install it with: pip install torch")
        raise


def load_model(model_name):
    try:
        import torch
        from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig
    except ImportError as e:
        logger.error("Required AI libraries not installed: %s", e)
        logger.error("Please install with: pip install torch transformers")
        raise

    device = detect_device()
    logger.info("Using device: %s", green(device))
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        dtype=torch.float16 if device != "cpu" else torch.float32,
    )
    model.eval()
    gen_config = GenerationConfig(
        max_new_tokens=MAX_NEW_TOKENS,
        max_length=None,
        do_sample=False,
        eos_token_id=tokenizer.eos_token_id,
    )
    return tokenizer, model, gen_config


def analyze_log_line_local(log_line, tokenizer, model, gen_config):
    prompt = f"Analyze this MongoDB log message and give me the answer in max 200 words: {str(log_line['msg'])}".strip()
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, generation_config=gen_config)
    text = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True).strip()

    return text


def analyze_log_line_gpt(log_line):
    """Analyze a MongoDB log line using OpenAI GPT API."""
    if ai_key == "":
        logger.warning("No AI API key found. Skipping AI analysis.")
        return ""

    # Support custom base_url for Azure OpenAI or other services
    base_url = os.environ.get("OPENAI_BASE_URL")
    client = OpenAI(
        api_key=ai_key,
        base_url=base_url if base_url else None,
    )

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a MongoDB export. Analyze MongoDB log messages and tell me the reason in max 200 words.",
                },
                {"role": "user", "content": str(log_line)},
            ],
            max_tokens=MAX_NEW_TOKENS,
            temperature=0.3,  # Lower temperature for more focused responses
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Failed to analyze log line with GPT: %s", e)
        return ""
