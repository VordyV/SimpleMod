import inspect
import os

__events = {}
__possible_events = []

def add_event(name):
	global __possible_events
	if name in __possible_events: raise Exception("Event %s has already been added" % name)
	return True

def __add_event_plugin(plugin_name, name, args):
	global __events
	if plugin_name not in __events:
		__events[plugin_name] = []
	__events[plugin_name].append((name, args))
	return

def plugin_events(plugin_name):
	return __events.get(plugin_name, [])

def events():
	return __events

def event(*args_event):
	frame = inspect.currentframe().f_back
	path = inspect.getframeinfo(frame).filename
	module = os.path.basename(path[:-3])
	def decorator(function):
		def wrapper(*args, **kwargs):
			return function(*args, **kwargs)
		__add_event_plugin(module, function.__name__, args_event)
		return wrapper
	return decorator