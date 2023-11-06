import threading
import os

os.environ['OPENAI_API_KEY']="sk-111111111111111111111111111111111111111111111111"
os.environ['OPENAI_API_BASE']="http://localhost:8081/v1"

import openai


def get_response(i, user_text, messages):
    send = messages.copy()
    send.append({'role': 'user', 'content': user_text})
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=send,
        temperature=0.5,
        stream=True
    )
    
    result = ''
    for chunk in response:
        delta = chunk['choices'][0]['delta']
        if 'content' in delta:
            chunk_text = chunk['choices'][0]['delta']['content']
            print(chunk_text, f'({i})', end='', flush=True)
            result += chunk_text

    print()
    print('Assistant', i)
    print(result)
    return result

def main():
    messages = [
        {'role': 'system', 'content': "You are a wise old sage. Answer questions from passersby."},
    ]
    
    user_texts = ["Hello, old man", "Tell me some wisdom", "what is the universe?"]

    threads = []
    for i, user_text in enumerate(user_texts):
        thread = threading.Thread(target=get_response, args=(i, user_text, messages))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()