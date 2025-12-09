from openai import OpenAI
import requests, time, os

# ---------- Client setup ----------
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ---------- Import corpus ----------
data_url = 'https://raw.githubusercontent.com/nemegrod/graph_RAG/refs/heads/main/data/jaguar_corpus.txt'

try:
    response = requests.get(data_url)
    response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
    corpus = response.text
    print(f"Successfully loaded text from {data_url}. Content length: {len(corpus)} characters.")
except requests.exceptions.RequestException as e:
    print(f"Error fetching ontology from {data_url}: {e}")


prompt = f"""
The word 'jaguar' can mean different things. What are the main meanings used in this text? 
Extract some examples of each from the text.
Be very concise in the result minimising the number of words used.

Text:
{corpus}
"""

    # "gpt-5",
    # "gpt-4o",
    # "gpt-4-turbo",

# ---------- Models to compare ----------
models_to_test = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4o",
    "gpt-5",
]

# ---------- Run test ----------
results = {}

for model in models_to_test:
    print(f"\n=== Testing {model} ===")
    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": (prompt[:-3200] if model=="gpt-4" else prompt) }],   
            temperature=(1 if model == "gpt-5" else 0)        
        )
        elapsed = time.time() - start

        # Token info lives under response.usage
        usage = getattr(response, "usage", None)
        usage_info = {
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        } if usage else {"prompt_tokens": None, "completion_tokens": None, "total_tokens": None}

        

        print(f"✅ Success in {elapsed:.2f}s | tokens: {usage_info['total_tokens']}")
        print(response.choices[0].message.content)
        results[model] = {
            "status": "success",
            "time": elapsed,
            "usage": usage_info,
            "output": response,
        }

    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ {model} failed in {elapsed:.2f}s: {e}")
        results[model] = {"status": "error", "time": elapsed, "error": str(e)}

# ---------- Summary ----------
print("\n=== Summary ===")
for m, info in results.items():
    usage = info.get("usage", {})
    print(
        f"{m:12} | {info['status']:8} | {info['time']:.2f}s | "
        f"{usage.get('total_tokens')} tokens (prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')})"
    )
