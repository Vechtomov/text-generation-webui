import os

os.environ["OPENAI_API_KEY"]="sk---anystringhere"
# os.environ["OPENAI_API_BASE"]="http://localhost:6001/v1"
os.environ["OPENAI_API_BASE"]="http://localhost:5001/v1"

import openai
import json

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)

def message_to_user(message):
    print(message)

def run_conversation():
    # Step 1: send the conversation and available functions to GPT
    functions = [
        {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
        {
            "name": "message_to_user",
            "description": "Sends a message to user",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message",
                    },
                },
                "required": ["message"],
            },
        },
    ]

    
    messages = [
        {"role": "system", "content": '''# MISSION
You are a large language model that assists users in interfacing with an API similar to OpenAI's. 
You will be provided with a list of available functions. 
When users interact with you, analyze their requests and respond with a JSON object that indicates:
1. The most appropriate function from the list they should call.
2. The arguments required for that function.
When the system executes the proposed function it could return to you the result of execution and you need to analyse the result and respond to the previous user request considering the given result.
         
# EXAMPLE:
Available functions:
[
    {
        "name": "calculate_price",
        "description": "Calculates a price for purchases.",
        "parameters": {
            "type": "object",
            "properties": {
                "product":{
                    "type": "string",
                    "description": "Name of a product",
                },
                "amount": {
                    "type": "integer",
                    "description": "Amount of a product",
                },
            },
            "required": ["product", "amount"],
        },
    },
    {
        "name": "answer_question",
        "description": "Provides answer to user question",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message of answer",
                },
            },
            "required": ["message"],
        },
    },
]
User: "What is the capital of France?"
Model: { "function": "answer_question", "arguments": { "message": "The capital of France is Paris." } }
User: "I want to buy 2 apples, how much will it cost?"
Model: { "function": "calculate_price", "arguments": { "product": "apple", "amount": 2 } }
Function Call Result: "0.6$"
Model: { "function": "answer_question", "arguments": { "message": "2 apples will cost you 0.6$." } }
                  
# AVAILABLE FUNCTIONS:
''' + json.dumps(functions, indent=2)},
        {"role": "user", "content": "What's the weather like in Boston?"}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        # function_call="auto",  # auto is default, but we'll be explicit
    )
    response_message = response["choices"][0]["message"]

    print(response_message)

    # Step 2: check if GPT wanted to call a function
    if response_message.get("function_call"):
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_current_weather": get_current_weather,
            "message_to_user": message_to_user
        }  # only one function in this example, but you can have multiple
        # print(response)
        function_name = response_message["function_call"]["name"]
        fuction_to_call = available_functions[function_name]
        function_args = json.loads(response_message["function_call"]["arguments"])
        function_response = fuction_to_call(
            **function_args
            # location=function_args.get("location"),
            # unit=function_args.get("unit"),
        )
        messages.append(response_message)  # extend conversation with assistant's reply

        if function_name == "get_current_weather":
            # Step 4: send the info on the function call and function response to GPT
            messages.append(
                {
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            )  # extend conversation with function response
        else:
            messages.append(
                {
                    "role": "user",
                    "content": input("User: "),
                }
            )
        second_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=functions,
        )  # get a new response from GPT where it can see the function response
        return second_response


print(run_conversation())