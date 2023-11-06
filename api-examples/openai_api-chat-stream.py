import os
os.environ['OPENAI_API_KEY']="sk-111111111111111111111111111111111111111111111111"
# os.environ['OPENAI_API_BASE']="https://073b-94-158-59-221.ngrok-free.app/v1"
os.environ['OPENAI_API_BASE']="http://localhost:5001/v1"
# os.environ['OPENAI_API_BASE']="http://localhost:8081/v1"

import openai

if __name__ == "__main__":
    with open('system-prompt.txt', 'r', encoding='utf-8') as f:
        system_prompt = f.read()
    messages = [
        { 'role': 'system', 'content': system_prompt},
    ]

    while True:
        user_text = input("User: ")
        messages.append({'role': 'user', 'content': user_text})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = messages,
            temperature=0.1,
            stream=True
        )

        print("Assistant: ", end='')
        assistant_message = ''
        for chunk in response:
            delta = chunk['choices'][0]['delta']
            # print(delta)
            if 'content' in delta:
                chunk_text = delta['content'].replace('<|im_end|>', '').replace('<|im_start|>', '')
                print(chunk_text, end='', flush=True)
                assistant_message += chunk_text

        assistant_message = assistant_message.replace('<|im_end|>', '').replace('<|im_start|>', '')
        
        # print(assistant_message)
        print()

        messages.append({'role': 'assistant', 'content': assistant_message})
        