import os
os.environ["HF_HOME"] = "/workspaces/hf-cache"

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

print("Loading Mistral model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir="/workspaces/hf-cache")

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    cache_dir="/workspaces/hf-cache",
    device_map="cpu"
)

print("Model loaded successfully.")

def generate(prompt: str):
    inputs = tokenizer(prompt, return_tensors="pt")

    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        temperature=0.7
    )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)