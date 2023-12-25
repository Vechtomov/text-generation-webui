import os
os.environ["OPENAI_API_BASE"] = "http://192.168.4.122:5001/v1"
os.environ["OPENAI_API_KEY"] = "anything"

import openai
import json
import re
import traceback

COMMANDS = {}

def command(func):
    command_name = func.__name__
    docstring: str = func.__doc__.strip()
    description, args_part = map(lambda x: x.strip(), docstring.split("Args:"))

    # Updated regex pattern to capture enum values
    args_pattern = r"(\w+) \((\w+)\)(?: \[([^\]]+)\])?: (.+)"
    arguments = {}
    for match in re.findall(args_pattern, args_part):
        enum_values: str = ""
        arg_name, arg_type, enum_values, description = match
        arg_info = {"type": arg_type, "description": description}
        if enum_values:
            arg_info["enum"] = [value.strip(" \"'") for value in enum_values.split(",")]
        arguments[arg_name] = arg_info

    COMMANDS[command_name] = {
        "function": func,
        "description": description,
        "arguments": arguments,
    }
    return func


# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
# @command
def get_current_weather(location: str, unit: str = "fahrenheit"):
    """
    Get the current weather in a given location.

    Args:
        location (string): The location to get the weather for.
        unit (string) ["celsius", "fahrenheit"]: The unit of temperature.
    """
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)


@command
def write_file(filename: str, text: str):
    """
    Writes text to the specified file.

    Args:
        filename (string): Name of the file.
        text (string): Text to write into the file.
    """
    try:
        with open(filename, "w") as f:
            f.write(text)
    except Exception:
        error_message = traceback.format_exc()
        return error_message


@command
def read_file(filename: str):
    """
    Reads and returns content from a file.

    Args:
        filename (string): Name of the file to read.
    """
    try:
        with open(filename, "r") as f:
            return f.read()
    except Exception:
        error_message = traceback.format_exc()
        return error_message


language = "eng"


@command
def get_language():
    """
    Returns current language.

    Args:
    """
    return language


@command
def set_language(lang: str):
    """
    Sets language.

    Args:
        lang (string) ['rus', 'eng', 'uzn']: Language.
    """
    global language
    language = lang
    print(language)


def execute_command(command: dict):
    print("Command: ", command)
    res = input("Execute this command? (Enter to confirm or explain reject): ")
    if res != "":
        return None, res

    command_name = command["name"]
    command_to_call = COMMANDS[command_name]
    command_result = command_to_call["function"](**command["arguments"])
    return command_name, command_result


def generate_functions_list():
    command_list = []
    for name, details in COMMANDS.items():
        command_properties = {}
        for arg, prop in details["arguments"].items():
            arg_properties = {"type": prop["type"]}
            if "enum" in prop:
                arg_properties["enum"] = prop["enum"]
            command_properties[arg] = arg_properties

        command_list.append(
            {
                "name": name,
                "description": details["description"],
                "parameters": {
                    "type": "object",
                    "properties": command_properties,
                },
            }
        )

    return command_list


def run_conversation():
    functions = generate_functions_list()

    messages = [
        {
            "role": "user",
            "content": input("User: "),
        },
    ]

    while True:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages, functions=functions
        )
        response_message = response["choices"][0]["message"]

        try:
            if "function_call" in response_message:
                command = {
                    "name": response_message["function_call"]["name"],
                    "arguments": json.loads(
                        response_message["function_call"]["arguments"]
                    ),
                }
                command_name, command_result = execute_command(command)
            else:
                command_name, command_result = None, None
                messages.append(
                    {
                        "role": "assistant",
                        "content": response_message["content"],
                    }
                )
                print("Assistant:", response_message["content"])
        except KeyboardInterrupt:
            return
        except:
            print(traceback.format_exc())
            print()
            print("Response: ", response_message)
            command_name = None
            command_result = "Invalid function call"

        if command_name is not None:
            msg = {
                "role": "function",
                "name": command_name,
                "content": command_result or "Success",
            }
        else:
            msg = {
                "role": "user",
                "content": input("User: "),
            }

        messages.append(msg)


run_conversation()
