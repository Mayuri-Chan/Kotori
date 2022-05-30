from bottle import request, route, response
from kotori.bot import bot
from kotori.db import data as data_db, user as db
from apiclient import errors
from datetime import datetime
from kotori import OWNER, app_url, gd_service
from kotori.web_modules.helpers import validate_secret

@route('/files', method='GET')
def files():
	user_id = request.params.user_id
	file_owner = False
	bot_owner = False
	if request.get_cookie('secret'):
		secret = request.get_cookie('secret')
		if secret != "Not_registered":
			user_data = validate_secret(secret)
			if user_data['status'] == 0:
				response.set_cookie('secret', '')
			else:
				if not user_id:
					user_id = user_data['user_id']
				if str(user_data['user_id']) == str(user_id):
					file_owner = True
				if str(user_data['user_id']) == str(OWNER):
					bot_owner = True
	if not user_id:
		response.set_header('Content-Type', 'application/json')
		return {"status": False, "reason": "user_id required!"}
	user_status = db.check_user(user_id)
	user_name = user_status.user_name
	response.set_cookie('last_pageid', str(user_id))
	if request.params.page:
		page = int(request.params.page)
	else:
		page = 1
	limit = 10
	offset = (page-1)*limit
	data_count = data_db.count_data(user_id)
	if data_count == 0:
		response.set_header('Content-Type', 'application/json')
		return {"status": False, "reason": "No files found!"}
	text = "<!DOCTYPE html>\n"
	text += '<html xmlns="http://www.w3.org/1999/xhtml">\n'
	text += "<head>\n"
	if file_owner:
		text += "<title>My Files</title>\n"
	else:
		text += "<title>Files by @{}</title>\n".format(user_name)
	text += '<meta charset="UTF-8" />\n'
	text += "</head>\n"
	text += '<body>\n<table width="100%" border=1>\n<tr>'
	if file_owner or bot_owner:
		text += '<th colspan="4">'
	else:
		text += '<th colspan="3">'
	if file_owner:
		text += 'My Files</th><th>'
	else:
		text += 'Files uploaded by <a href="https://t.me/{}">@{}</a></th><th>'.format(user_name,user_name)	
	if request.get_cookie('secret'):
		if request.get_cookie('secret') == "Not_registered":
			text += "<img style='height: 50px' src='{}' alt='Profile Pic' /><br /><a href='https://t.me/{}'>{}</a> (Not registered) [<a href='logout'>Logout</a>]".format(request.get_cookie('photo'),request.get_cookie('user_name'),request.get_cookie('user_name'))
		else:
			text += "<img style='height: 50px' src='{}' alt='Profile Pic' /><br /><a href='https://t.me/{}'>{}</a> [<a href='logout'>Logout</a>]".format(user_data['photo'],user_data['user_name'],user_data['user_name'])
	else:
		text += '<script async src="https://telegram.org/js/telegram-widget.js?19" data-telegram-login="{}" data-size="medium" data-auth-url="login" data-request-access="write"></script>'.format(bot.getMe().username)
	text += '</th></tr>\n<tr><th>No</th><th>Filename</th><th>Download</th>'
	if file_owner or bot_owner:
		text += '<th>Delete</th>'
	text += '<th>Upload Date</th></tr>'
	n = 1
	data = data_db.get_data(user_id,limit,offset)
	for x in data:
		text += "\n<tr><td style='text-align:center;'>{}</td><td style='text-align:center;'>{}</td><td style='text-align:center;'><a href='https://drive.google.com/file/d/{}?view'>Google Drive</a> | <a href='{}/d/{}'>Direct</a></td>".format(n,x.file_name,x.file_id,app_url,x.file_id)
		if file_owner or bot_owner:
			text += "<td style='text-align:center;'><a href='delete?id={}&user_id={}'>Delete</a></td>".format(x.file_id,user_id)
		text += "<td style='text-align:center;'>{}</td></tr>".format(datetime.fromtimestamp(x.time))
		n = n+1
	text += "\n</table>\n</body>\n</html>"
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
