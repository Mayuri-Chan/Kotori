from kotori import OWNER
from kotori.bot import ALL_MOD, HELPABLE_MOD, HELPABLE_OWNER, bot, dispatcher
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CommandHandler, Filters

def bot_start(update, context):
	args = context.args
	chat = update.effective_chat
	message = update.effective_message
	if message.chat.type != "private":
		message.reply_text("Send me message in PM.")
		return
	if len(args) >= 1:
		if args[0].lower().startswith("gen_"):
			return asyncio.run(gen_file(update,context))
		if args[0].lower() == "help":
			return bot_help(update, context)
	keyboard = InlineKeyboardMarkup(
		[[InlineKeyboardButton(text="Help", url=f"t.me/{bot.getMe().username}?start=help")]])
	message.reply_text("Hello!\nThis bot is under development.",reply_markup=keyboard)

def bot_help(update, context):
	args = context.args
	chat = update.effective_chat
	message = update.effective_message
	user_id = update.effective_user.id
	if len(args) >= 1 and args[0] != "help":
		module = args[0]
		if module in HELPABLE_OWNER:
			if module == "owner" and str(user_id) != str(OWNER):
				return message.reply_text("Could not found module {}.".format(module))
			text = ALL_MOD[module].__help__
			return message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
		return message.reply_text("Could not found module {}.".format(module))
	if str(user_id) != str(OWNER):
		HELPABLE = HELPABLE_MOD
	else:
		HELPABLE = HELPABLE_OWNER
	HELP_STRINGS = f"""
	You can use / to execute bot commands.
	*Main* commands which available:
	- /start: get start message
	- /help: get help message
	- /help <module> : get module help message
	
	All module: `{"`, `".join(HELPABLE)}`
	"""
	dispatcher.bot.send_message(
		chat_id=chat.id,
		text=HELP_STRINGS,
		parse_mode=ParseMode.MARKDOWN,
		disable_web_page_preview=True
	)

start_handler = CommandHandler('start', bot_start, pass_args=True)
help_handler = CommandHandler('help', bot_help)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(help_handler)
