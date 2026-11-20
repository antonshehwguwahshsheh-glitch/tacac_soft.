import os
import time
import random
import string
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
import database as db

# --- Токен и админ ---
BOT_TOKEN = "9159488529:AAHF04FlzQbOo7jk27v8AeMKiLzRal9JSLE"
ADMIN_ID = 0  # <--- ВСТАВЬ СЮДА СВОЙ ЦИФРОВОЙ ID (узнать у @userinfobot)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Клавиатуры ---
def start_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить чит", callback_data="shop")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🔑 Активировать ключ", callback_data="activate")],
        [InlineKeyboardButton(text="📱 Сбросить HWID (10 ⭐)", callback_data="reset_hwid")],
    ])

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="🔑 Активировать ключ", callback_data="activate")],
        [InlineKeyboardButton(text="📱 Сбросить HWID (10 ⭐)", callback_data="reset_hwid")],
    ])

def shop_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="7 дней — 25 ⭐", callback_data="buy_7")],
        [InlineKeyboardButton(text="30 дней — 50 ⭐", callback_data="buy_30")],
        [InlineKeyboardButton(text="60 дней — 100 ⭐", callback_data="buy_60")],
        [InlineKeyboardButton(text="Навсегда — 200 ⭐", callback_data="buy_forever")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_start")],
    ])

# --- Команды ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await db.create_user(message.from_user.id)
    welcome_text = (
        "👋 **Добро пожаловать в tacac_soft!**\n\n"
        "Хочешь приобрести крутой чит?\n"
        "Покупай у нас! Работаем **строго с root-правами**.\n\n"
        "Выбери действие ниже:"
    )
    await message.answer(welcome_text, reply_markup=start_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_start")
async def back_start_cb(call: types.CallbackQuery):
    welcome_text = (
        "👋 **Добро пожаловать в tacac_soft!**\n\n"
        "Хочешь приобрести крутой чит?\n"
        "Покупай у нас! Работаем **строго с root-правами**.\n\n"
        "Выбери действие ниже:"
    )
    await call.message.edit_text(welcome_text, reply_markup=start_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "back")
async def back_cb(call: types.CallbackQuery):
    await call.message.edit_text("Главное меню:", reply_markup=main_menu())
    await call.answer()

@dp.callback_query(F.data == "profile")
async def profile_cb(call: types.CallbackQuery):
    user = await db.get_user(call.from_user.id)
    if not user:
        return await call.answer("Нажми /start")
    _, hwid, sub_end = user
    now = int(time.time())
    sub_text = f"Активна, осталось {(sub_end - now)//86400} дн." if sub_end > now else "Не активна"
    text = f"👤 **Профиль**\n\nID: `{call.from_user.id}`\nHWID: `{hwid or 'не привязан'}`\nПодписка: {sub_text}"
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="back_start")]]), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data == "shop")
async def shop_cb(call: types.CallbackQuery):
    await call.message.edit_text("🛒 **Магазин подписок**\nВыбери срок:", reply_markup=shop_menu(), parse_mode="Markdown")
    await call.answer()

@dp.callback_query(F.data.startswith("buy_"))
async def buy_cb(call: types.CallbackQuery):
    prices = {"buy_7": (25,"7 дней"), "buy_30": (50,"30 дней"), "buy_60": (100,"60 дней"), "buy_forever": (200,"Навсегда")}
    stars, label = prices[call.data]
    await bot.send_invoice(call.from_user.id, title=f"Подписка {label}", description=f"Доступ к tacac_soft на {label}", payload=call.data, provider_token="", currency="XTR", prices=[LabeledPrice(label=label, amount=stars)])
    await call.answer()

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)

@dp.message(F.successful_payment)
async def payment_done(message: types.Message):
    payload = message.successful_payment.invoice_payload
    if payload == "reset_hwid":
        await db.reset_hwid(message.from_user.id)
        await message.answer("✅ HWID сброшен. Теперь можешь привязать новое устройство.")
    else:
        days_map = {"buy_7": 7, "buy_30": 30, "buy_60": 60, "buy_forever": 36500}
        days = days_map.get(payload, 0)
        if days:
            await db.add_subscription(message.from_user.id, days)
            await message.answer(f"✅ Подписка активирована на {days} дн. Спасибо за покупку!")

@dp.callback_query(F.data == "reset_hwid")
async def reset_hwid_cb(call: types.CallbackQuery):
    await bot.send_invoice(call.from_user.id, title="Сброс HWID", description="Отвязка устройства", payload="reset_hwid", provider_token="", currency="XTR", prices=[LabeledPrice(label="Сброс", amount=10)])
    await call.answer()

@dp.callback_query(F.data == "activate")
async def activate_cb(call: types.CallbackQuery):
    await call.message.edit_text("Отправь ключ в чат:")
    await call.answer()

@dp.message(F.text.regexp(r"^[A-Z0-9-]{10,}$"))
async def key_input(message: types.Message):
    ok = await db.activate_key(message.from_user.id, message.text.strip().upper())
    await message.answer("✅ Ключ активирован!" if ok else "❌ Ключ недействителен или использован.")

@dp.message(Command("genkey"))
async def genkey_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        return await message.answer("Использование: /genkey <дни>")
    days = int(args[1])
    key = "TACAC-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=12))
    await db.create_key(key, days)
    await message.answer(f"🔑 Ключ на {days} дн.: `{key}`", parse_mode="Markdown")

async def main():
    await db.init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
