from datetime import datetime
from flask import redirect
from flask_login import current_user
import random


def generate_random_password():
	characters = "1234567890QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm"
	length = 12

	return "".join([random.choice(characters) for _ in range(length)])


def generate_school_code():
	characters = "QWERTYUIOPASDFGHJKLZXCVBNM"
	
	return "".join([random.choice(characters) for _ in range(8)])


def to_unix_timestamp(timestamp):
	try:
		dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")

		return int(dt.timestamp())
	except:
		return None
	

def timestamp_to_local(timestamp):
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp).isoformat(timespec="minutes")


def admin_required(func):
	def wrapper(*args, **kwargs):
		if not current_user.is_authenticated:
			return redirect("/")

		if not current_user.role.name == "admin":
			return redirect("/")

		return func(*args, **kwargs)
	
	wrapper.__name__ = func.__name__
	
	return wrapper


def logout_required(func):
	def wrapper(*args, **kwargs):
		if current_user.is_authenticated:
			return redirect("/")
		
		return func(*args, **kwargs)
	
	wrapper.__name__ = func.__name__

	return wrapper


def check_object_exists(classtype, redir_to, key_name="id"):
	def decorator(func):
		def wrapper(**kwargs):
			kw_dict = { key_name: kwargs[list(kwargs.keys())[0]] }
			obj = classtype.query.filter_by(**kw_dict).first()

			if not obj:
				return redirect(redir_to)
			
			return func(obj)
		
		wrapper.__name__ = func.__name__
		return wrapper

	return decorator