import asyncio
import base64
import importlib
import telegram

from kotori import BOT_TOKEN, OWNER, owner_alias
from kotori.bot_modules import ALL_MODULES
from kotori.db import user as db
from telegram import  InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CommandHandler, Filters, Updater

updater = Updater(token=BOT_TOKEN, use_context=True)
dispatcher = updater.dispatcher

bot = telegram.Bot(token=BOT_TOKEN)

owner_status = db.check_user(OWNER)
if not owner_status:
	s = "{} {} {}".format(OWNER,owner_alias,time.time())
	owner_secret = base64.b64encode(s.encode('utf-8')).decode('utf-8')
	db.add_to_users(OWNER, owner_secret, owner_alias, 1, '')

def send_text(chat_id, text, btn, pin):
	m = bot.send_message(text=text, chat_id=chat_id, reply_markup=btn, parse_mode=ParseMode.HTML)
	if pin:
		m.pin()

ALL_MOD = {}
HELPABLE_MOD = []
HELPABLE_OWNER = []
IMPORTED = {}
print("Loading modules...")

for module_name in ALL_MODULES:
	imported_module = importlib.import_module("kotori.bot_modules." + module_name)
	if not hasattr(imported_module, "__mod_name__"):
		imported_module.__mod_name__ = imported_module.__name__

	if not imported_module.__mod_name__.lower() in IMPORTED:
		IMPORTED[imported_module.__mod_name__.lower()] = imported_module
	else:
		raise Exception("Can't have two modules with the same name! Please change one")

	if hasattr(imported_module, "__help__") and imported_module.__help__:
		if module_name != "owner":
			HELPABLE_MOD.append(module_name)
		HELPABLE_OWNER.append(module_name)
		ALL_MOD[module_name] = imported_module

print("----------------------------------------------------------------")
print(" Loaded Bot Modules : ["+", ".join(ALL_MODULES)+"]")
print("----------------------------------------------------------------")

updater.start_polling()
