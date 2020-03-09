import json
import datetime, random

def load_survey():
    with open("survey_pt.json") as json_file:
        return json.load(json_file)["questions"]



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
    