from bottle import error, response

@error(404)
def not_found(_):
	response.set_header('Content-Type', 'application/json')
	return '{"status": 404, "reason": "Page Not Found!"}'

@error(405)
def not_allowd(_):
	response.set_header('Content-Type', 'application/json')
	return '{"status": 405, "reason": "Method Not Allowed!"}'
