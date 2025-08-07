from transformers import AutoModelForCausalLM, AutoTokenizer, GPTQConfig

model_name = "Qwen/Qwen3-4B-Instruct-2507"

# load the tokenizer and the model
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "play_english_audio",
            "description": "播放英语音频"
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop_english_audio",
            "description": "停止播放英语音频"
        },
    },
    {
        "type": "function",
        "function": {
            "name": "other_requirement",
            "description": "如果用户的请求是其他类型，请调用这个函数"
        }
    }
]

# prepare the model input
prompt = """
你是一个智能终端，目前只支持播放/停止播放英语音频的功能，请根据后续用户的提示，调用指定的函数以执行对应的操作。如果用户的意图，不属于 播放英语音频/停止播放英语音频 中的任何一种，请调用other_requirement函数
"""

prompt_list = [
    "播放音频",
    "播放",
    "停止播放",
    "别播了",
    "停下来",
    "你好",
    "今天天气如何"
]

for prompt in prompt_list:
    messages = [
        {"role": "user", "content": prompt}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tools=TOOLS,
        tokenize=False,
        add_generation_prompt=True,
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    # conduct text completion
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=512
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist()

    content = tokenizer.decode(output_ids, skip_special_tokens=True)

    print(f"prompt: {prompt}, response: {content}")
