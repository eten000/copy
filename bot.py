from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio
import os

API_TOKEN = '7936997110:AAHoUpcqsnTswLN3sRX307J4N5aLrj-BR5g'
ADMIN_ID = 951399170  # 👈 Вставь сюда свой Telegram ID
CHANNEL_USERNAME = '@copyrayter1'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# FSM для заказа и отзыва
class OrderState(StatesGroup):
    waiting_for_task = State()
    waiting_for_urgency = State()
    waiting_for_file = State()

class FeedbackState(StatesGroup):
    waiting_for_feedback = State()

# Клавиатура
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📋 Услуги", callback_data="services"),
     InlineKeyboardButton(text="💰 Цены", callback_data="prices")],
    [InlineKeyboardButton(text="📝 Сделать заказ", callback_data="order")],
    [InlineKeyboardButton(text="⭐ Отзывы", callback_data="reviews"),
     InlineKeyboardButton(text="💬 Отправить отзыв", callback_data="feedback")],
    [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
])

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! Я помогу вам с копирайтингом, дизайном и не только.\n\n"
        "Выберите, что вас интересует:",
        reply_markup=main_menu
    )

@dp.callback_query(F.data == "services")
async def services(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔧 *Услуги:*\n\n"
        "— Набор текста, копирайтинг ✍️\n"
        "— Презентации, оформление в Canva 🎨\n"
        "— Таблицы, документы 📄\n"
        "— PDF, транскрибация 🎧\n"
        "— Лёгкий дизайн 🖌️",
        parse_mode="Markdown",
        reply_markup=main_menu
    )

@dp.callback_query(F.data == "prices")
async def prices(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "💰 *Цены:*\n\n"
        "Минимальная стоимость — *от 300₽*.\n"
        "Срочные заказы — по договорённости.",
        parse_mode="Markdown",
        reply_markup=main_menu
    )

@dp.callback_query(F.data == "help")
async def help_section(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "❓ *Помощь:*\n\n"
        "Если что-то непонятно — просто напишите мне.\n"
        "Я отвечу как можно скорее!",
        parse_mode="Markdown",
        reply_markup=main_menu
    )

@dp.callback_query(F.data == "order")
async def start_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📝 Опишите, пожалуйста, что нужно сделать:")
    await state.set_state(OrderState.waiting_for_task)

@dp.message(OrderState.waiting_for_task)
async def get_task(message: Message, state: FSMContext):
    await state.update_data(task=message.text)
    await message.answer("⏱ Это срочно? (Да / Нет)")
    await state.set_state(OrderState.waiting_for_urgency)

@dp.message(OrderState.waiting_for_urgency)
async def get_urgency(message: Message, state: FSMContext):
    await state.update_data(urgency=message.text)
    await message.answer("📎 Если есть файл — отправьте его.\nЕсли нет — напишите 'нет'.")
    await state.set_state(OrderState.waiting_for_file)

@dp.message(OrderState.waiting_for_file)
async def get_file(message: Message, state: FSMContext):
    user_data = await state.get_data()
    task = user_data['task']
    urgency = user_data['urgency']
    username = message.from_user.username or message.from_user.full_name

    file_info = "Файла нет."
    if message.document:
        file_info = f"📎 Прикреплён файл: {message.document.file_name}"

    text = (
        f"🆕 *Новый заказ*\n\n"
        f"👤 От: @{username}\n"
        f"📝 Задача: {task}\n"
        f"⏱ Срочность: {urgency}\n"
        f"{file_info}"
    )

    # Отправка админу и в канал
    await bot.send_message(ADMIN_ID, text, parse_mode="Markdown")
    await bot.send_message(CHANNEL_USERNAME, text, parse_mode="Markdown")
    if message.document:
        await bot.send_document(ADMIN_ID, message.document)
        await bot.send_document(CHANNEL_USERNAME, message.document)

    await message.answer("✅ Спасибо! Ваш заказ отправлен.")
    await state.clear()

# -------------------- Отзыв --------------------

@dp.callback_query(F.data == "feedback")
async def start_feedback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("💬 Напишите свой отзыв:")
    await state.set_state(FeedbackState.waiting_for_feedback)

@dp.message(FeedbackState.waiting_for_feedback)
async def get_feedback(message: Message, state: FSMContext):
    username = message.from_user.username or message.from_user.full_name
    feedback = f"⭐ От @{username}:\n{message.text}\n---\n"

    # Сохраняем в файл
    with open("reviews.txt", "a", encoding="utf-8") as f:
        f.write(feedback)

    await bot.send_message(ADMIN_ID, f"📝 Новый отзыв от @{username}:\n\n{message.text}")
    await message.answer("✅ Спасибо за отзыв!")
    await state.clear()

@dp.callback_query(F.data == "reviews")
async def show_reviews(callback: types.CallbackQuery):
    if not os.path.exists("reviews.txt"):
        await callback.message.edit_text("Пока что нет отзывов 😔", reply_markup=main_menu)
        return

    with open("reviews.txt", "r", encoding="utf-8") as f:
        lines = f.read().strip().split('---\n')
        last_reviews = lines[-5:] if len(lines) >= 5 else lines

    formatted = "\n\n".join(last_reviews).strip()
    if not formatted:
        formatted = "Пока что нет отзывов 😔"

    await callback.message.edit_text(f"⭐ *Отзывы:*\n\n{formatted}", parse_mode="Markdown", reply_markup=main_menu)

# --------------------

async def main():
    print("Бот запущен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())