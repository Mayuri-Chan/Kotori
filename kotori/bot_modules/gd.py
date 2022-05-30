import asyncio
import io
import math
import time

from kotori import OWNER, app_url, def_chat_id, folder_id, gd_service
from kotori.bot import dispatcher
from kotori.bot_modules.helpers import humanbytes, time_formatter
from kotori.db import user as db, data as data_db
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CommandHandler, Filters

async def get_information(service, Id):
	r = (
		service.files()
		.get(
			fileId=Id,
			fields="name, id, size, mimeType, "
			"webViewLink, webContentLink,"
			"description",
			supportsAllDrives=True,
		)
		.execute()
	)
	return r

def upload_to_gd(file_name,file_path):
	media_body = MediaFileUpload(
		file_path,
		resumable=True
	)

	body = {
		"name": file_name,
	}
	if folder_id:
		body["parents"] = folder_id

	file = gd_service.files().create(body=body, media_body=media_body,
								  fields="id").execute()

	file_id = file.get("id")
	permission = {
		"role": "reader",
		"type": "anyone"
	}

	gd_service.permissions().create(fileId=file_id, body=permission).execute()
	return file_id

async def gen_file(update, context):
	user_id = update.effective_user.id
	user_name = update.effective_user.username
	message = update.effective_message
	args = context.args
	if args[0].startswith("gen_"):
		file_id = args[0].replace("gen_", "")
	else:
		file_id = args[0]
	file_data = data_db.get_file(file_id)
	file = await get_information(gd_service, file_id)
	file_name = file.get("name")
	request = gd_service.files().get_media(fileId=file_id, supportsAllDrives=True)
	file_path = "tmp/{}".format(file_name)
	msg = message.reply_text("Downloading...")
	with io.FileIO(file_path, "wb") as df:
		downloader = MediaIoBaseDownload(df, request)
		complete = False
		current_time = time.time()
		display_message = None
		while complete is False:
			status, complete = downloader.next_chunk()
			if status:
				file_size = status.total_size
				diff = time.time() - current_time
				downloaded = status.resumable_progress
				percentage = downloaded / file_size * 100
				speed = round(downloaded / diff, 2)
				eta = round((file_size - downloaded) / speed)
				prog_str = "`Downloading` | [{}{}] `{}%`".format(
					"".join(["●" for i in range(math.floor(percentage / 10))]),
					"".join(["○" for i in range(10 - math.floor(percentage / 10))]),
					round(percentage, 2),
				)
				current_message = (
					"`[FILE - DOWNLOAD]`\n\n"
					f"`{file_name}`\n"
					f"`Status`\n{prog_str}\n"
					f"`{humanbytes(downloaded)} of {humanbytes(file_size)}"
					f" @ {humanbytes(speed)}`\n"
					f"`ETA` -> {time_formatter(eta)}"
				)
				if (
					round(diff % 15.00) == 0
					and (display_message != current_message)
					or (downloaded == file_size)
				):
					msg.edit_text(current_message, parse_mode=ParseMode.MARKDOWN)
					display_message = current_message
	file_link = "https://drive.google.com/file/d/{}/view".format(file_id)
	index_link = "{}/files?user_id={}".format(app_url,user_id)
	direct_link = "{}/d/{}".format(app_url,file_id)
	btn = InlineKeyboardMarkup([
		[InlineKeyboardButton(text="⬇️Download", url=file_link), InlineKeyboardButton(text="⬇️Direct", url=direct_link)],
		[InlineKeyboardButton(text="☁️Index", url=index_link)]
		])
	text = "File Name: {}\nSize: {}".format(file_name,humanbytes(file_size))
	msg.edit_text(text, reply_markup=btn, parse_mode=ParseMode.HTML)
