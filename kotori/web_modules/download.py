import os

from bottle import request, route, response, static_file
from kotori.bot import bot
from kotori.db import data as db

@route('/d/<id>', method="GET")
def download(id):
	file_id = id
	file_data = db.get_file(file_id)
	if not file_data:
		return {"status": False, "reason": "File not found!"}
	filename = file_data[0].file_name
	if os.path.exists("files/"+filename):
		return static_file(filename, root="files", download=filename)
	gen_url = "https://t.me/{}?start=gen_{}".format(bot.getMe().username,file_id)
	return "<h1>Link expired!</h1><br /><a href='{}'>click here</a> to regenerate".format(gen_url)
