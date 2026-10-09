import os
import traceback

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 1. Gemini API setup (preferred if GEMINI_API_KEY is present)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = None

if GEMINI_API_KEY:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini API client initialized successfully.")
    except Exception as e:
        print(f"Warning: Could not initialize Gemini client ({e}).")

# 2. Local HuggingFace model (Lazy loaded only when needed)
tokenizer = None
model = None

def _load_local_model():
    global tokenizer, model
    if model is None:
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
        except ImportError as err:
            raise RuntimeError(
                f"Local model requires 'torch' and 'transformers'. Install them or set GEMINI_API_KEY in .env: {err}"
            )

        MODEL_ID = os.getenv("LOCAL_MODEL_ID", "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
        cache_dir = os.getenv("HF_HOME", None)
        print(f"Loading local model {MODEL_ID}...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=cache_dir)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            cache_dir=cache_dir,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            torch_dtype=torch.float32
        )
        print("Local model loaded successfully.")

def generate(prompt: str) -> str:
    # Option A: Gemini API
    if gemini_client:
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            if response.text:
                return response.text
        except Exception as e:
            print(f"Gemini API generation failed: {e}. Falling back to local model...")

    # Option B: Local HuggingFace Transformer
    _load_local_model()

    import torch

    messages = [
        {
            "role": "system",
            "content": "You are a Schema.org and JSON-LD expert. You output ONLY valid JSON without markdown fences or extra explanations."
        },
        {"role": "user", "content": prompt}
    ]

    try:
        formatted_prompt = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
    except Exception:
        formatted_prompt = prompt

    inputs = tokenizer(formatted_prompt, return_tensors="pt")
    input_ids = inputs["input_ids"].to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            input_ids=input_ids,
            max_new_tokens=400,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode ONLY newly generated tokens (excluding prompt)
    generated_tokens = outputs[0][input_ids.shape[1]:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True)