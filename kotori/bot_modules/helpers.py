import re

from math import ceil
from typing import List, Dict
from telegram import InlineKeyboardButton

def time_formatter(seconds: int) -> str:
	minutes, seconds = divmod(seconds, 60)
	hours, minutes = divmod(minutes, 60)
	days, hours = divmod(hours, 24)
	tmp = (
		((str(days) + " day(s), ") if days else "")
		+ ((str(hours) + " hour(s), ") if hours else "")
		+ ((str(minutes) + " minute(s), ") if minutes else "")
		+ ((str(seconds) + " second(s), ") if seconds else "")
	)
	return tmp[:-2]

def humanbytes(size: int) -> str:
	if size is None or isinstance(size, str):
		return ""

	power = 2**10
	raised_to_pow = 0
	dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
	while size > power:
		size /= power
		raised_to_pow += 1
	return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"
