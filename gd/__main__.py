import asyncio
import os
import base64
import time
import json

from bottle import abort, request, route, run, static_file, error, response
from datetime import datetime
from gd import OWNER, app_url, chat_url, def_chat_id, gd_service, owner_alias, user_db as db, data_db
from gd.bot import bot, humanbytes, send_text
from googleapiclient.http import MediaFileUpload
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def validate_secret(secret):
	data = db.get_data(secret)
	if not data:
		return {"status": False, "reason": "Secret key not found!"}
	status = data[0].status
	if status == 0:
		return {"status": False, "reason": "You are banned!"}
	user_data = {"user_id": data[0].user_id, "secret": data[0].secret, "user_name": data[0].user_name, "status": data[0].status}
	return user_data

@error(404)
def not_found(_):
	response.set_header('Content-Type', 'application/json')
	return '{"status": 404, "reason": "Page Not Found!"}'

@error(405)
def not_allowd(_):
	response.set_header('Content-Type', 'application/json')
	return '{"status": 405, "reason": "Method Not Allowed!"}'

@route('/')
def index():
	response.status = 303
	response.set_header('Location', chat_url)

@route('/gd', method='POST')
def upload_gd():
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
		filename = document.filename
		chat = request.forms.get("chat_id")
		if chat:
			chat_id = int(chat)
			pin = False
		else:
			pin = True
			chat_id = def_chat_id

		file_path = "tmp/{}".format(document.filename)
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
		direct_link = "{}/download?id={}".format(app_url,file_id)
		btn = InlineKeyboardMarkup([
			[InlineKeyboardButton(text="⬇️Download", url=file_link), InlineKeyboardButton(text="⬇️Direct", url=direct_link)],
			[InlineKeyboardButton(text="☁️Index", url=index_link)]
			])
		send_text(chat_id, text, btn, pin)
		os.rename(file_path,"files/{}".format(document.filename))
		data_db.add_to_gddata(secret_status['user_id'],file_id,filename,time.time())
		return {"status": True, "file_name": filename, "file_size": file_size, "file_link": file_link}

@route('/files', method='GET')
def files():
	user_id = request.params.user_id
	user_status = db.check_user(user_id)
	user_name = user_status.user_name
	file_owner = False
	bot_owner = False
	if request.get_cookie('secret'):
		secret = request.get_cookie('secret')
		user_data = validate_secret(secret)
		if user_data['status'] == 0:
			response.set_cookie('secret', '')
		file_owner = True
		if user_data['user_id'] == OWNER:
			bot_owner = True
	if not user_id:
		response.set_header('Content-Type', 'application/json')
		return {"status": False, "reason": "user_id required!"}
	if request.params.page:
		page = request.params.page
	else:
		page = 1
	limit = 10
	offset = (page-1)*limit
	data_count = data_db.count_data(user_id)
	if data_count == 0:
		response.set_header('Content-Type', 'application/json')
		return {"status": False, "reason": "No files found!"}
	text = '<table width="100%" border=1><tr>'
	if file_owner or bot_owner:
		text += '<th colspan="4">'
	else:
		text += '<th colspan="3">'
	text += 'Files uploaded by <a href="https://t.me/{}">@{}</a></th><th>'.format(user_name,user_name)
	if request.get_cookie('secret'):
		text += '<a href="logout?user_id={}">Logout</a>'.format(user_id)
	else:
		text += '<a href="login?user_id={}">Login</a>'.format(user_id)
	text += '</th></tr><tr><th>No</th><th>Filename</th><th>Download</th>'
	if file_owner or bot_owner:
		text += '<th>Delete</th>'
	text += '<th>Upload Date</th></tr>'
	n = 1
	data = data_db.get_data(user_id,limit,offset)
	for x in data:
		text += "<tr><td style='text-align:center;'>{}</td><td style='text-align:center;'>{}</td><td style='text-align:center;'><a href='https://drive.google.com/file/d/{}?view'>Google Drive</a> | <a href='{}/download?id={}'>Direct</a></td>".format(n,x.file_name,x.file_id,app_url,x.file_id)
		if file_owner or bot_owner:
			text += "<td style='text-align:center;'><a href='delete?id={}&user_id={}'>Delete</a></td>".format(x.file_id,user_id)
		text += "<td style='text-align:center;'>{}</td></tr>".format(datetime.fromtimestamp(x.time))
		n = n+1
	text += "</table>"
	if data_count > limit:
		a = data_count/limit
		if a > int(a):
			max_page = int(a)+1
		else:
			max_page = int(a)
		if page != 1:
			text += "<a href='/files?user_id={}&page=1'><<</a> |".format(user_id)
			text += " <a href='/files?user_id={}&page={}'><</a> |".format(user_id,page-1)
		for i in range(1,max_page+1):
			if i == page:
				text += " {} |".format(i)
			else:
				text += " <a href='/files?user_id={}&page={}'>{}</a> |".format(user_id,i,i)
		if page != max_page:
			text += " <a href='/files?user_id={}&page={}'>></a> |".format(user_id,page+1)
			text += " <a href='/files?user_id={}&page={}'>>></a>".format(user_id,max_page)
	return text

@route('/download', method="GET")
def download():
	file_id = request.params.id
	file_data = data_db.get_file(file_id)
	if not file_data:
		return {"status": False, "reason": "File not found!"}
	filename = file_data[0].file_name
	if os.path.exists("files/"+filename):
		return static_file(filename, root="files", download=filename)
	gen_url = "https://t.me/{}?start=gen_{}".format(bot.getMe().username,file_id)
	return "<h1>Link expired!</h1><br /><a href='{}'>click here</a> to regenerate".format(gen_url)

@route('/login', method=["POST","GET"])
def login():
	user_id = request.params.user_id
	secret = request.params.secret
	if secret:
		user_data = validate_secret(secret)
		if user_data['status'] == 1:
			response.set_cookie('secret', secret)
			response.status = 303
			return response.set_header('Location', "files?user_id={}".format(user_id))
		response.set_header('Content-Type', 'application/json')
		return {"status": False, "reason": "Secret not found!"}
	text = "<form action='login?user_id={}' method='POST'>".format(user_id)
	text += "<table>"
	text += "<tr><td><input type='text' name='secret' placeholder='Secret' /></td><td style='text-align:center;' colspan='3'><input type='submit' value='Login' /></td></tr>"
	text += "</table></form>"
	return text

@route('/logout', method=["POST","GET"])
def logout():
	user_id = request.params.user_id
	response.set_cookie('secret', '')
	response.status = 303
	return response.set_header('Location', "files?user_id={}".format(user_id))

@route('/delete', method="GET")
def delete():
	user_id = request.params.user_id
	file_id = request.params.id
	secret = request.get_cookie('secret')
	if not file_id:
		response.set_header('Content-Type', 'application/json')
		return {"status": False, "reason": "File id required!"}
	if not secret:
		response.set_header('Content-Type', 'application/json')
		return {"status": False, "reason": "You need to login first!"}
	user_data = validate_secret(secret)
	if not user_data:
		response.status = 303
		return response.set_header('Location', "files?user_id={}".format(user_id))
	if user_data['user_id'] != user_id and user_data['user_id'] != OWNER:
		response.set_header('Content-Type', 'application/json')
		return {"status": False, "reason": "You don't have permission to delete this file!"}
	try:
		gd_service.files().delete(fileId=file_id).execute()
	except errors.HttpError as err:
		print(err)
	data_db.delete_from_gddata(file_id)
	response.status = 303
	response.set_header('Location', "files?user_id={}".format(user_id))

@route('/donate', method="GET")
def donate():
	response.status = 303
	response.set_header('Location', "https://t.me/wulan17/4")

if __name__ == "__main__":
	run(host='0.0.0.0', port=os.environ.get('PORT', '5000'))
