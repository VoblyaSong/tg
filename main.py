import asyncio
import re  
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router
from aiogram.enums import ParseMode

TOKEN = '8117709260:AAGscZ7bD-IC5qoQNdTiA9cYbB0ZxvWaZ6A'
ADMIN_ID = 5091334393

bot = Bot(TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

countries = ["Франция", "Германия", "Грузия", "Италия", "Испания", "Швеция"]

country_names_en = {
    "Франция": "France",
    "Германия": "Germany",
    "Грузия": "Georgia",
    "Италия": "Italy",
    "Испания": "Spain",
    "Швеция": "Sweden"
}

class VotingStates(StatesGroup):
    choosing_country = State()
    entering_name = State()
    sending_scores = State()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=country)] for country in countries
    ] + [[KeyboardButton(text="Отмена")]])
    await state.set_state(VotingStates.choosing_country)
    await message.answer("Жюри какой страны вы представляете?", reply_markup=keyboard)

@router.message(F.text.lower() == "отмена")
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text=country)] for country in countries
    ] + [[KeyboardButton(text="Отмена")]])
    await state.set_state(VotingStates.choosing_country)
    await message.answer(
        "Действие отменено. Выберите страну жюри, чтобы начать заново:",
        reply_markup=keyboard
    )

@router.message(VotingStates.choosing_country)
async def handle_country_choice(message: types.Message, state: FSMContext):
    if message.text not in countries:
        await message.answer("Пожалуйста, выберите страну из списка или нажмите 'Отмена'.")
        return
    await state.update_data(country=message.text)
    await state.set_state(VotingStates.entering_name)
    await message.answer("Кто представит баллы вашей страны?")

@router.message(VotingStates.entering_name)
async def handle_name_input(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(VotingStates.sending_scores)
    await message.answer(
        "Прекрасно! Теперь отправляйте свои голоса по системе Евровидения (1-8, 10, 12)\n\nФормат:\n12 - Страна\n10 - Страна\n...\n\nЕсли хотите отменить — отправьте 'Отмена'.",
        reply_markup=types.ReplyKeyboardRemove()
    )

@router.message(VotingStates.sending_scores)
async def handle_scores(message: types.Message, state: FSMContext):
    text = message.text.strip()
    pattern = r"(1[0-2]|[1-9])\s*-\s*(.+)"
    matches = re.findall(pattern, text)

    expected_points = {'12', '10', '8', '7', '6', '5', '4', '3', '2', '1'}
    submitted_points = set()
    countries_voted = []
    points_dict = {}

    for point, country in matches:
        submitted_points.add(point)
        countries_voted.append(country.strip().lower())
        points_dict[point] = country.strip()

    missing = sorted(expected_points - submitted_points, reverse=True)
    if missing:
        await message.answer(f"⚠️ Пожалуйста, отправьте все баллы! Отсутствуют: {', '.join(missing)}")
        return

    duplicates = [country for country in countries_voted if countries_voted.count(country) > 1]
    if duplicates:
        unique_duplicates = sorted(set(duplicates))
        await message.answer(f"⚠️ Страны не должны повторяться. Повторы: {', '.join(unique_duplicates)}")
        return

    user_data = await state.get_data()
    jury_country_ru = user_data.get('country', 'Неизвестно')
    jury_country_en = country_names_en.get(jury_country_ru, jury_country_ru)

    formatted = (
        f'["Country"] = "{jury_country_en}",\n'
        f'   ["Name"] = "{user_data.get("name", "")}",\n'
        f'   ["Background"] = "",\n'
        f'   ["12 points"] = "{points_dict.get("12", "")}",\n'
        f'   ["10 points"] = "{points_dict.get("10", "")}",\n'
        f'   ["8 points"] = "{points_dict.get("8", "")}",\n'
        f'   ["7 points"] = "{points_dict.get("7", "")}",\n'
        f'   ["6 points"] = "{points_dict.get("6", "")}",\n'
        f'   ["5 points"] = "{points_dict.get("5", "")}",\n'
        f'   ["4 points"] = "{points_dict.get("4", "")}",\n'
        f'   ["3 points"] = "{points_dict.get("3", "")}",\n'
        f'   ["2 points"] = "{points_dict.get("2", "")}",\n'
        f'   ["1 points"] = "{points_dict.get("1", "")}")n'
    

    await bot.send_message(chat_id=ADMIN_ID, text=f"<code>{formatted}</code>", parse_mode=ParseMode.HTML)

    await message.answer("Спасибо, баллы приняты.")
    await state.clear()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
