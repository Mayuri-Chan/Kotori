from kotori.db import user as db

def validate_secret(secret):
	data = db.get_data(secret)
	if not data:
		return {"status": False, "reason": "Secret key not found!"}
	status = data[0].status
	if status == 0:
		return {"status": False, "reason": "You are banned!"}
	user_data = {"user_id": data[0].user_id, "secret": data[0].secret, "user_name": data[0].user_name, "status": data[0].status, "photo": data[0].photo}
	return user_data
