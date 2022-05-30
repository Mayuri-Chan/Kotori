import time

from bottle import request, route, response
from datetime import datetime
from kotori import OWNER 
from kotori.bot import send_text
from kotori.db import user as db

@route('/login', method=["GET"])
def login():
	user_id = request.params.id
	last_pageid = request.get_cookie('last_pageid')
	if not request.get_cookie('secret') or request.get_cookie('secret') == 'Not_registered':
		username = request.params.username
		first_name = request.params.first_name
		check_user = db.check_user(user_id)
		photo_url = request.params.photo_url
		expires = time.mktime(datetime.max.timetuple())
		if check_user:
			if check_user.user_name != username and str(user_id) != str(OWNER):
				db.add_to_users(user_id,check_user.secret,username,1, photo_url)
			if not check_user.photo or check_user.photo != request.params.photo_url:
				db.add_to_users(user_id,check_user.secret,username,1, photo_url)
			response.set_cookie('secret', check_user.secret, expires=expires)
		else:
			response.set_cookie('secret', "Not_registered")
			response.set_cookie('user_name', username, expires=expires)
			response.set_cookie('photo', photo_url, expires=expires)
		text = "Kamu berhasil login ke web sebagai <a href='tg://user?id={}'>{}</a>.".format(user_id,first_name)
		send_text(user_id, text, None, False)
	response.status = 303
	response.set_header('Location', "files?user_id={}".format(last_pageid))

@route('/logout', method=["GET"])
def logout():
	last_pageid = request.get_cookie('last_pageid')
	response.set_cookie('secret', '', expires=0)
	response.set_cookie('user_name', '', expires=0)
	response.set_cookie('photo', '', expires=0)
	response.status = 303
	response.set_header('Location', "files?user_id={}".format(last_pageid))
