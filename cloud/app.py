import json
import threading
import gradio as gr
import spaces
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODELS = {
    "Paper 1.2": "HuggingFaceTB/SmolLM2-360M-Instruct",
    "Marble 1.5": "Qwen/Qwen2.5-0.5B-Instruct",
    "Opal 2.1": "Qwen/Qwen2.5-Coder-1.5B-Instruct",
}
# Keep model weights on CPU until a GPU is allocated.
models = {}
for name, model_id in MODELS.items():
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype=torch.bfloat16).eval()
    models[name] = (tokenizer, model)

@spaces.GPU(duration=45)
def generate(name, prompt, history_json, max_tokens):
    if name not in models:
        raise gr.Error("Неизвестная модель")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
        raise gr.Error("Введите сообщение до 12000 символов")
    limit = max(16, min(512, int(max_tokens)))
    history = json.loads(history_json or "[]")
    if not isinstance(history, list):
        raise gr.Error("Неверная история")
    messages = [{"role": "system", "content": f"Ты {name}, ассистент приложения Solune. Отвечай на конкретный последний вопрос пользователя, по-русски, если запрос на русском. Не повторяй приветствие. Ты адаптированная открытая модель. /code — код; /deep — подробный анализ; /instant — краткий ответ; /img — SVG."}]
    for m in history[-8:]:
        if isinstance(m, dict) and m.get("role") in ("user","assistant") and isinstance(m.get("content"), str):
            messages.append({"role":m["role"],"content":m["content"][-3000:]})
    messages.append({"role":"user","content":prompt})
    tokenizer, model = models[name]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    tokenizer.truncation_side = "left"
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=2048).to("cuda")
    model = model.to("cuda")
    try:
        with torch.inference_mode():
            output = model.generate(**inputs, max_new_tokens=limit, do_sample=False, repetition_penalty=1.08, pad_token_id=tokenizer.eos_token_id)
        return tokenizer.decode(output[0, inputs.input_ids.shape[1]:], skip_special_tokens=True).strip()
    finally:
        model.to("cpu")
        torch.cuda.empty_cache()

with gr.Blocks(title="Solune Cloud") as demo:
    gr.Markdown("# Solune Cloud\nExperimental shared GPU inference. Do not submit private information.")
    name = gr.Dropdown(list(MODELS), value="Marble 1.5", label="Модель")
    prompt = gr.Textbox(label="Запрос", lines=4)
    history = gr.Textbox(value="[]", visible=False)
    tokens = gr.Slider(16,512,value=160,step=16,label="Максимум токенов")
    result = gr.Textbox(label="Ответ")
    gr.Button("Отправить").click(generate,[name,prompt,history,tokens],result,api_name="generate",concurrency_limit=1)
demo.queue(max_size=8).launch()
