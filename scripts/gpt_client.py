from openai import OpenAI

client = None


def init_client():
    global client
    if client is None:
        client = OpenAI(base_url='https://40.chatgptsb.net/v1',
                        api_key='sk-BAAcqM5uwpwL6QpbkxfEJ4yfJQXx05sbBMJIxKH8WdhZ9jUM', timeout=600.0)


def chat_completion(user_prompt, system_prompt='', model='gpt-4.1'):
    init_client()
    messages = []
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    messages.append({
        "role": "user",
        "content": user_prompt
    })
    response = client.chat.completions.create(messages=messages, model=model)
    return response.choices[0].message.content, response.usage.prompt_tokens, response.usage.completion_tokens
