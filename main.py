import logging
import settings
import os
from utils import load_survey, get_current_question, write_survey, write_survey2, already_answered

import aiogram.utils.markdown as md
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode

API_TOKEN = os.getenv("TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# template survey
template = load_survey()

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
# dp = Dispatcher(bot)
# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


users = {}

# States
class Form(StatesGroup):
    imdb = State() 
    imdb_comment = State() 


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` command
    """
    await message.reply(f"Olá {message.chat.first_name}, irei fazer algumas perguntas sobre a sua experiência com o [bot].")
    await message.answer("Envie o comando /survey_imdb para que possamos começar o questionário.")


@dp.message_handler(commands=['survey_imdb'])
async def send_survey(message: types.Message):
    

    if already_answered(message.from_user.id):
        # Configure ReplyKeyboardMarkup
        markup = types.ReplyKeyboardMarkup()
        markup.add("sim", "não")

        await message.answer("Você já respondeu esse questionário, deseja refazer?", reply_markup=markup)

    else:
        await resend_imdb_survey(message)
    
async def resend_imdb_survey(message):
    keyboard_markup = types.InlineKeyboardMarkup()
    # Set state
    await Form.imdb.set()
    keyboard_markup.row(types.InlineKeyboardButton("próxima", callback_data="next_1"))
    question_1 = template[0]
    await bot.send_poll(message.chat.id, question=question_1["text"], 
                        options=question_1["options"], allows_multiple_answers=question_1["allows_multiple_answers"],
                        reply_markup=keyboard_markup,
                        is_anonymous=False
                        )


@dp.message_handler(lambda message: message.text in ["sim", "não"])
async def process_resend_survey(message: types.Message):
    if message.text == "sim":
        await message.reply(f"O questionário anterior foi desconsiderado.", reply_markup=types.ReplyKeyboardRemove())
        await resend_imdb_survey(message)
    else:
        await message.reply(f"Tudo bem então, até outro momento ;)", reply_markup=types.ReplyKeyboardRemove())


@dp.callback_query_handler(regexp='(^next_[0-9]*$)', state=Form.imdb)
async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):
    keyboard_markup = types.InlineKeyboardMarkup()
    _, index = query.data.split("_")
    index  = int(index)
    poll = await bot.stop_poll(query.message.chat.id, query.message.message_id)
    write_survey(index, query.message.chat.id, poll)
    value, question = get_current_question(template, index)
    if value == 1:
        index += 1
        keyboard_markup.row(types.InlineKeyboardButton("próxima", callback_data=f"next_{index}"))
        await query.bot.send_poll(query.message.chat.id, question["text"], question["options"], 
             allows_multiple_answers=question["allows_multiple_answers"], is_anonymous=False, reply_markup=keyboard_markup)
    else:
        await query.message.answer(question["text"])
        await Form.next()
    await state.update_data(index=int(index))

@dp.message_handler(state=Form.imdb_comment)
async def imdb_comment(message: types.Message, state: FSMContext):
    # old style:
    # await bot.send_message(message.chat.id, message.text)
    async with state.proxy() as data:
        index = int(data["index"]) + 1

    write_survey2(message.from_user.id, template[index-1]["text"], message.text)

    has_question, question = get_current_question(template, index)
    if has_question:
        await message.answer(question["text"])
        await state.update_data(index=index)
    else:
        # Finish conversation
        await message.answer(question)
        await state.finish()
    

# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Cancelled.')


if __name__ == '__main__':
    executor.start_polling(dp)