import threading

from kotori import BASE, SESSION
from sqlalchemy import Column, BigInteger, Integer, String, UnicodeText

class Users(BASE):
	__tablename__ = "users"
	user_id = Column(BigInteger, primary_key=True)
	secret = Column(UnicodeText)
	user_name = Column(UnicodeText)
	status = Column(Integer)
	photo = Column(UnicodeText)

	def __init__(self,user_id,secret,user_name,status,photo):
		self.user_id = user_id
		self.secret = secret
		self.user_name = user_name
		self.status = status
		self.photo = photo

	def __repr__(self):
		return "<Users '%s'>" % (self.user_id)

Users.__table__.create(checkfirst=True)

USERS_INSERTION_LOCK = threading.RLock()

def add_to_users(user_id,secret,user_name,status,photo):
	with USERS_INSERTION_LOCK:
		prev = SESSION.query(Users).get((user_id))
		if prev:
			SESSION.delete(prev)
			SESSION.commit()

		users_filt = Users(user_id,secret,user_name,status,photo)

		SESSION.merge(users_filt)
		SESSION.commit()

def get_data(secret):
	try:
		return SESSION.query(Users).filter(Users.secret == secret).all()
	finally:
		SESSION.close()

def check_user(user_id):
	try:
		return SESSION.query(Users).get(user_id)
	finally:
		SESSION.close()
