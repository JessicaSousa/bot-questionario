import logging
import settings
import os


from utils import load_survey, get_current_question, write_survey, write_survey2

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.deep_linking import get_start_link
from aiogram.dispatcher.filters.builtin import CommandStart

API_TOKEN = os.getenv("TOKEN")

# Configure logging
logging.basicConfig(level=logging.INFO)

# template survey
# template = load_survey()

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
# dp = Dispatcher(bot)
# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


users = {}

# States
class Form(StatesGroup):
    poll = State()
    comment = State()


@dp.message_handler(CommandStart("imdbot"))
async def start_imdb(message: types.Message):
    await resend_imdb_survey(message, "imdbot")


@dp.message_handler(CommandStart("qualisbot"))
async def start_qualis_bot(message: types.Message):
    await message.answer("Você selecionou qualis bot.")


@dp.message_handler(commands='start')
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` command
    """
    imdbot = await get_start_link('imdbot')
    qualisbot = await get_start_link('qualisbot')
    keyboard_markup = types.InlineKeyboardMarkup()
    keyboard_markup.row(types.InlineKeyboardButton("IMDB", url=imdbot))
    keyboard_markup.row(types.InlineKeyboardButton("Qualis", url=qualisbot))
    

    await message.reply(f"Olá {message.chat.first_name}, algum dos seguintes bot te encaminhou até aqui para responder"\
        " um questionário, peço que selecione a opção correspondente a esse bot.", reply_markup=keyboard_markup)


async def resend_imdb_survey(message, bot_name):
    keyboard_markup = types.InlineKeyboardMarkup()
    # Set state
    await Form.poll.set()

    template = load_survey(bot_name)

    keyboard_markup.row(types.InlineKeyboardButton("próxima", callback_data=f"{bot_name}_next_1"))
    question_1 = template[0]
    await bot.send_poll(message.chat.id, question=question_1["text"], 
                        options=question_1["options"], allows_multiple_answers=question_1["allows_multiple_answers"],
                        reply_markup=keyboard_markup,
                        is_anonymous=False
                        )


@dp.callback_query_handler(regexp=r'(^[a-z]*bot_next_[\d]*$)', state=Form.poll)
async def inline_kb_answer_callback_handler(query: types.CallbackQuery, state: FSMContext):
    keyboard_markup = types.InlineKeyboardMarkup()
    bot_name,_, index = query.data.split("_")
    index  = int(index)
    poll = await bot.stop_poll(query.message.chat.id, query.message.message_id)
    write_survey(index, query.message.chat.id, poll, bot_name)
    async with state.proxy() as data:
        if "survey" not in data:
            template = load_survey(bot_name)
            await state.update_data(survey=template)
            await state.update_data(bot_name=bot_name)
        else:
            template = data["survey"]
    value, question = get_current_question(template, index)
    if value == 1:
        index += 1
        keyboard_markup.row(types.InlineKeyboardButton("próxima", callback_data=f"{bot_name}_next_{index}"))
        await query.bot.send_poll(query.message.chat.id, question["text"], question["options"], 
             allows_multiple_answers=question["allows_multiple_answers"], is_anonymous=False, reply_markup=keyboard_markup)
    else:
        
        await query.message.answer(question["text"])
        await Form.next()
    await state.update_data(index=int(index))
    

@dp.message_handler(state=Form.comment)
async def imdb_comment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        index = int(data["index"]) + 1
        template = data["survey"]
        bot_name = data["bot_name"]

    write_survey2(message.from_user.id, template[index-1]["text"], message.text, bot_name)

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