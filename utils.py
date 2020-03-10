import json
import os
import datetime, random

def load_survey():
    with open("survey_pt.json") as json_file:
        return json.load(json_file)["questions"]


def write_survey(index, user_id, poll, bot_name="imdb_bot"):
    options = poll["options"]
    mode = "w" if index == 1 else "a"
    with open(f"data/{user_id}_{bot_name}.txt", mode) as f:
        f.write(f"[{poll['question']}]\n")
        for option in options:
            op = option["text"]
            is_voted = "✔️" if bool(option["voter_count"]) else ""
            f.write(f"{op}: {is_voted}\n")
        f.close()


def write_survey2(user_id, question, text, bot_name="imdb_bot"):
    with open(f"data/{user_id}_{bot_name}.txt", "a") as f:
        f.write(f"[{question}]\n")
        f.write(f"R.: {text}\n")
        f.close()


def already_answered(user_id, bot_name="imdb_bot"):
    return os.path.isfile(f'data/{user_id}_{bot_name}.txt')

def greetings():
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        return " bom dia"
    elif 12 <= current_hour < 18:
        return 'a boa tarde.'
    return 'a boa noite!'


def get_current_question(template, index):
    if index < len(template):
        options = template[index]["options"]
        if options:
            return 1, template[index] # enquete
        return -1, template[index] # pergunta simples
    return 0, f"Agradeço por você ter avaliado o bot, tenha um{greetings()}."
    