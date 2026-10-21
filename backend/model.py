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

def set_gemini_api_key(api_key: str) -> bool:
    global GEMINI_API_KEY, gemini_client
    if not api_key or not api_key.strip():
        return False
    try:
        from google import genai
        GEMINI_API_KEY = api_key.strip()
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        return True
    except Exception as e:
        print(f"Failed to set Gemini API key: {e}")
        return False

def is_gemini_configured() -> bool:
    return gemini_client is not None

def test_gemini() -> dict:
    if not gemini_client:
        return {
            "configured": False,
            "working": False,
            "error": "GEMINI_API_KEY environment variable is not set."
        }
    
    models_to_try = [
        os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        "gemini-2.5-flash",
        "gemini-1.5-flash"
    ]
    last_error = None
    for m_name in models_to_try:
        try:
            res = gemini_client.models.generate_content(
                model=m_name,
                contents="Say 'OK' if you can read this."
            )
            return {
                "configured": True,
                "working": True,
                "model": m_name,
                "response": res.text.strip() if res.text else "OK"
            }
        except Exception as e:
            last_error = str(e)
            print(f"Test with {m_name} failed: {e}")

    return {
        "configured": True,
        "working": False,
        "error": last_error
    }

if GEMINI_API_KEY:
    set_gemini_api_key(GEMINI_API_KEY)

# 2. Local HuggingFace model (Lazy loaded only when needed)
tokenizer = None
model = None

def load_local_model():
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
        is_cuda = torch.cuda.is_available()

        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=cache_dir)

        if is_cuda:
            try:
                from transformers import BitsAndBytesConfig
                print(f"Loading local model {MODEL_ID} in 4-bit precision on GPU (VRAM optimized)...")
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4"
                )
                model = AutoModelForCausalLM.from_pretrained(
                    MODEL_ID,
                    cache_dir=cache_dir,
                    device_map="cuda",
                    quantization_config=bnb_config
                )
            except Exception as q_err:
                print(f"4-bit loading fallback to float16: {q_err}")
                model = AutoModelForCausalLM.from_pretrained(
                    MODEL_ID,
                    cache_dir=cache_dir,
                    device_map="cuda",
                    dtype=torch.float16
                )
            vram_gb = torch.cuda.memory_allocated() / (1024 ** 3)
            print(f"Local model loaded successfully in GPU VRAM ({torch.cuda.get_device_name(0)}). VRAM used: {vram_gb:.2f} GB")
        else:
            print(f"Loading local model {MODEL_ID} on CPU...")
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_ID,
                cache_dir=cache_dir,
                device_map="cpu",
                dtype=torch.float32
            )
            print("Local model loaded successfully in CPU RAM.")

def _load_local_model():
    load_local_model()

def generate(prompt: str) -> str:
    # Option A: Gemini API
    if gemini_client:
        models_to_try = [
            os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            "gemini-2.5-flash",
            "gemini-1.5-flash"
        ]
        for m_name in models_to_try:
            try:
                response = gemini_client.models.generate_content(
                    model=m_name,
                    contents=prompt
                )
                if response.text:
                    return response.text
            except Exception as e:
                print(f"Gemini API generation failed with model {m_name}: {e}. Trying fallback...")

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

    inputs = tokenizer(formatted_prompt, return_tensors="pt", max_length=1500, truncation=True)
    input_ids = inputs["input_ids"].to(model.device)
    attention_mask = inputs.get("attention_mask")
    if attention_mask is not None:
        attention_mask = attention_mask.to(model.device)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    if hasattr(model, "generation_config"):
        model.generation_config.max_length = None

    with torch.inference_mode():
        outputs = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=450,
            do_sample=True,
            temperature=0.3,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    # Decode ONLY newly generated tokens (excluding prompt)
    generated_tokens = outputs[0][input_ids.shape[1]:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True)
