import ast
import json

from ai_bot import Bot
from files_viewer import FilesViewer

def print_dict_list(dict_list):
    print("[")
    for i, d in enumerate(dict_list):
        print("    {")
        for key, value in d.items():
            lines = value.split("\\n")
            print(f"        \"{key}\": \"{lines[0]}\",")
            for line in lines[1:]:
                print(f"        \"    {line}\",")
        print("    }" + ("," if i < len(dict_list) - 1 else ""))
    print("]")

def handle_command(response, fv):
    lines = response.splitlines()
    command = "[]"
    for line in lines:
        if line.startswith('open ['):
            command = line[line.index('['):]
            entry = ast.literal_eval(command)
            fv.open(entry)
        if line.startswith('close ['):
            command = line[line.index('['):]
            entry = ast.literal_eval(command)
            fv.close(entry)

def main():
    starter_msg = """
You are a memory sensitive AI coding bot, fully autonomous, its up to you to decide where to look and what to do to solve the initial goal. 
Do not ask the user for direction, you will make decisions and choose what to see and what to change.
You will have a Memory Window which is used to for managing what part of the project you see.
Since your memory is limited you need to only see what is necessary to solve the immediate task.

You will be able to open a file, function, class, or others. 
Open something like so:
open ["file.py", "class:myclass", "func:myfunc"]
This will open the function myfunc in the class myclass in the file file.py
Do it with the actual names obviously.
Upon opening something, your memory window will be updated with the contents.

After you have opened enough you can suggest code changes. Specify to which file and which functions/classes

You can also specify to close a file, function, or class. Similar to opening them

Each prompt you will have the choice between opening, closing, or propose a code change. You are able to open multiple times.
Each command must be on a separate line, ex:
open []
open []
close []

The Memory Window is what you will use to understand the section of the repository you need to understand. If a key is pointed to 'None' that means its closed and can be opened.
If its pointed to an empty datastructure, that means its empty and already opened.

Also, at the bottom please provide a line for what you want to remember, like your current thought process.

Full output format you must follow each time, only output the 3 categories as shown below:
Commands:
open []
# add more as needed

Changes:
# propose changes if any be necessary

Memory:
# a line for what your current thoughts are or what you have done and why
"""
    bot = Bot(init_prompt=starter_msg)
    project_dir = input("Welcome to codefullgpt, to start, enter the location of your project: ")
    fv = FilesViewer(project_dir)
    main_goal = input("Enter main goal: ")
    prev = "I have not done anything yet. I will choose something to open"
    bot.message_log.append(None)
    while True:
        user_input = input("Tell something to AI (Optional): ")
        assistant_mem = f"""
Main goal: {main_goal}

Memory Window:
{fv.view_window_to_string()}

Available Memory Tokens:
7777

What I did/thought last time: {prev.splitlines()[-1]}
"""
        bot.message_log[1] = {"role": "assistant", "content": assistant_mem}
        avail = bot.get_remaining_tokens()
        bot.message_log[1]["content"] = bot.message_log[1]["content"].replace("7777", str(avail))
        response = bot.send_to_openai(user_input, save_mem=False, output_token_length=6000)
        prev = response
        
        print("\n\n")
        print_dict_list(bot.message_log)
        
        print("\n")
        print(f"Leftover tokens: {bot.leftover_tokens}")
        print(f"AI response:\n{response}\n")
        
        proceed = input("Do you want to proceed with the command the AI has given? (y or (empty) will continue) ")
        if not proceed or proceed.lower().startswith("y"):
            handle_command(response, fv)

    

if __name__ == '__main__':
    main()
