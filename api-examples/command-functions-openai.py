import os

os.environ["OPENAI_API_KEY"] = "sk---anystringhere"
os.environ["OPENAI_API_BASE"] = "http://localhost:5001/v1"

import openai
import json
import re
import sys
import traceback
import io

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
            # arg_info["enum"] = [value.strip() for value in enum_values.split(",")]
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
def execute_python_code(code: str):
    """
    Executes a given string of Python code and returns it's output.

    Args:
        code (string): Python code to execute.
    """
    if not code:
        return "Code shouldn't be empty"

    old_stdout = sys.stdout  # Save the current stdout
    new_stdout = io.StringIO()  # Create a string buffer to capture output
    sys.stdout = new_stdout

    try:
        exec(code)
        return new_stdout.getvalue()  # Return captured output
    except Exception:
        error_message = traceback.format_exc()
        return error_message
    finally:
        sys.stdout = old_stdout  # Restore original stdout


# @command
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


# @command
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


@command
def finish(result: str):
    """
    Finishes the task and provides the result to user.

    Args:
        result (string): The result of the task.
    """
    print("Task result: ", result)


# @command
def ask_user(question: str):
    """
    Ask the user a question. Use this command only if you get stuck.

    Args:
        question (string): Question.
    """
    print("Question: ", question)
    return input("User: ")


def create_command(thoughts: str, command: dict):
    if not thoughts:
        return None, "Thoughts should be provided"

    print("Thoughts: ", thoughts)
    print("Command: ", command)
    res = input("Execute this command? (Enter to confirm or explain reject): ")
    if res != "":
        return None, res

    command_name = command["name"]
    command_to_call = COMMANDS[command_name]
    command_result = command_to_call["function"](**command["arguments"])
    return command_name, command_result


def generate_commands_message():
    messages = []
    for i, (name, details) in enumerate(COMMANDS.items(), 1):
        description = details["description"]
        arguments = ", ".join(
            [
                f"{arg}: {info['type']} {info['enum'] if 'enum' in info else ''}"
                for arg, info in details["arguments"].items()
            ]
        )
        message = f"{i}. {name}: {description} Params: ({arguments})"
        messages.append(message)
    return "\n".join(messages)


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
                "type": "object",
                "properties": {
                    "name": {"const": name},
                    "arguments": {"type": "object", "properties": command_properties},
                },
            }
        )

    functions_list = [
        {
            "name": "create_command",
            "description": "Creates a command that will be executed",
            "parameters": {
                "type": "object",
                "properties": {
                    "thoughts": {
                        "type": "object",
                        "description": "Your thoughts about user's task and what command could fit this task.",
                        "properties": {
                            "observations": {
                                "description": "Relevant observations from your last action (if any)",
                                "type": "string",
                                "required": True,
                            },
                            "reasoning": {
                                "description": "Thoughts",
                                "type": "string",
                                "required": True,
                            },
                            "self_criticism": {
                                "description": "Constructive self-criticism",
                                "type": "string",
                                "required": True,
                            },
                            "plan": {
                                "description": "Short markdown-style bullet list that conveys the long-term plan",
                                "type": "string",
                                "required": True,
                            },
                            "speak": {
                                "description": "Summary of thoughts, to say to user",
                                "type": "string",
                                "required": True,
                            },
                        },
                    },
                    "command": {
                        "description": "Command that will be executed",
                        "type": "",
                        "oneOf": command_list,
                    },
                },
            },
        }
    ]

    return functions_list


def run_conversation():
    functions = generate_functions_list()

    messages = [
        {
            "role": "system",
            "content": f"""You are a 200 IQ genius. 
You have Sherlock Holmes and Tony Stark minds combined.
Your reasoning skills and python knowledge are fantastic.
If you fail, you don't give up, explore hypothesis and learn on given result.
You solve user's tasks step by step by creating commands that will be executed. 
After sending the command you will get the command results or user's instructions.
Given the current conversation you decide what command should be executed next and send this command to user.
You don't ask user questions until you get really stuck.
The list of the commands you can use:
{generate_commands_message()}
""",
        },
        {
            "role": "user",
            "content": "I have a task for you but I don't remember the filename of the task file. Look in the current directory",
        },
    ]

    while True:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=functions,
            function_call={"name": "create_command"},
        )
        response_message = response["choices"][0]["message"]
        messages.append(response_message)

        try:
            function_args = json.loads(response_message["function_call"]["arguments"])
            command_name, command_result = create_command(**function_args)
        except KeyboardInterrupt:
            return
        except:
            print(traceback.format_exc())
            print()
            print("Response: ", response_message)
            command_name = None
            command_result = "Invalid function call"

        if command_name is not None and command_name != "finish":
            messages.append(
                {
                    "role": "user",
                    "content": "Command result: " + command_result,
                }
            )
        else:
            messages.append(
                {
                    "role": "user",
                    "content": command_result or input("User: "),
                }
            )


run_conversation()
