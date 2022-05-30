import os
import time

from bottle import request, route, response
from googleapiclient.http import MediaFileUpload
from kotori import OWNER, app_url, def_chat_id, gd_service
from kotori.bot import send_text
from kotori.bot_modules.helpers import humanbytes
from kotori.db import data as db
from kotori.web_modules.helpers import validate_secret
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

@route('/gd', method='POST')
def gd():
	response.set_header('Content-Type', 'application/json')
	secret = request.params.get('secret')
	if not secret:
		return {"status": False, "reason": "Secret key required!"}
	secret_status = validate_secret(secret)
	if secret_status:
		if secret_status['status'] == 0:
			return secret_status
		os.system("rm -rf tmp/*")
		document = request.files.get('document')
		filename, file_ext = os.path.splitext(document.filename)
		dupe = True
		file_num = 0
		while dupe:
			if file_num != 0:
				file_status = db.check_file("{}-{}{}".format(filename,file_num,file_ext))
			else:
				file_status = db.check_file("{}{}".format(filename,file_ext))
			if file_status:
				file_num = file_num+1
			else:
				if file_num == 0:
					filename = "{}{}".format(filename,file_ext)
				else:
					filename = "{}-{}{}".format(filename,file_num,file_ext)
				dupe = False
		chat = request.forms.get("chat_id")
		if chat:
			chat_id = int(chat)
			pin = False
		else:
			pin = True
			chat_id = def_chat_id

		file_path = "tmp/{}".format(filename)
		document.save(file_path)
		file_size = humanbytes(os.path.getsize(file_path))

		media_body = MediaFileUpload(
			file_path,
			resumable=True
		)

		body = {
			"name": filename,
		}

		file = gd_service.files().create(body=body, media_body=media_body,
									  fields="id").execute()

		file_id = file.get("id")
		permission = {
			"role": "reader",
			"type": "anyone"
		}

		gd_service.permissions().create(fileId=file_id, body=permission).execute()

		if secret_status['user_id'] == OWNER:
			text = "File Name: {}\nSize: {}\n\nUploaded by: <a href='tg://user?id={}'>{}</a>".format(filename,file_size,secret_status['user_id'],secret_status['user_name'])
		else:
			text = "File Name: {}\nSize: {}\n\nUploaded by: @{}".format(filename,file_size,secret_status['user_name'])
		file_link = "https://drive.google.com/file/d/{}/view".format(file_id)
		index_link = "{}/files?user_id={}".format(app_url,secret_status['user_id'])
		direct_link = "{}/d/{}".format(app_url,file_id)
		btn = InlineKeyboardMarkup([
			[InlineKeyboardButton(text="⬇️Download", url=file_link), InlineKeyboardButton(text="⬇️Direct", url=direct_link)],
			[InlineKeyboardButton(text="☁️Index", url=index_link)]
			])
		send_text(chat_id, text, btn, pin)
		os.rename(file_path,"files/{}".format(document.filename))
		db.add_to_gddata(secret_status['user_id'],file_id,filename,time.time())
		return {"status": True, "file_name": filename, "file_size": file_size, "file_link": file_link}
