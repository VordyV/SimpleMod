import logging
import logging.config
import sys
import yaml
import datetime
import host
import importlib
import os
import imp
import simplefuncs

class Config():

	defaultOptions = {}
	options = {}
	filename = "simplemod.yml"

	def implement(self):
		file = open(self.filename, "a")
		file.close()
		self.read()

		for key, value, in self.defaultOptions.items():
			self.options[key] = self.options.get(key, value)

		self.write()

	def read(self):
		file = open(self.filename, "r")
		data = yaml.safe_load(file)
		file.close()
		if data is None: data = {}
		self.options = data

	def write(self):
		file = open(self.filename, "w")
		yaml.dump(self.options, file)
		file.close()
		return True

	def addDefOptions(self, **kwargs):
		self.defaultOptions.update(kwargs)
		return True

	def get(self, option, default_value=None):
		keys = option.split('.')
		value = self.options
		for key in keys:
			value = value.get(key, default_value)
			if value is None:
				break
		return value

	def set(self, option, value):
		self.options[option] = value
		return self.write()

class Event(object):
	def __init__(self, name, method, args):
		self.name = name
		self.method = method
		self.args = args

class Plugin(object):
	def __init__(self, name, module, plugin):
		self.module = module
		self.name = name
		self.plugin = plugin

PL_ATTR_NAME = 'name'
PL_ATTR_VERSION = 'version'
PL_ATTR_DEVELOPERS = 'developers'
PL_ATTR_REQUIRED_PLUGINS = 'required_plugins'

PL_EVENT_ENABLE = 'onEnable'
PL_EVENT_DISABLE = 'onDisable'

class SimpleMod(object):

	name = "Simple Mod"
	version = "0.0.2"
	developer = ""

	def __init__(self):
		self.config = Config()
		self.config.addDefOptions(
			sm_logs_filename='simplemod.log',
			sm_logs_dir='logs',
			sm_logs_path='%Y_%m_%d.log',
			sm_logs_encoding='utf-8',
			sm_logs_format='%(asctime)s: %(name)s: %(levelname)s| %(message)s',
			sm_plugin_dir='admin/plugins',
			sm_plugins=[],
		)

		self.config.implement()

		if not os.path.exists(self.config.get('sm_plugin_dir')):
			os.makedirs(self.config.get('sm_plugin_dir'))

		sys.path.append( self.config.get('sm_plugin_dir') )


		logging.basicConfig(filename=self.config.get('sm_logs_filename'), level=logging.DEBUG, format=self.config.get('sm_logs_format'))

		fileHandlerHis = logging.FileHandler(datetime.datetime.now().strftime("%s/%s"%(self.config.get('sm_logs_dir'), self.config.get('sm_logs_path'))), mode="a", encoding=self.config.get('sm_logs_encoding'))
		fileHandlerHis.setLevel(logging.DEBUG)

		formatter = logging.Formatter(self.config.get('sm_logs_format'))

		fileHandlerHis.setFormatter(formatter)

		logging.getLogger().addHandler(fileHandlerHis)

		self.__plugins = {}
		self.__events = {}

	def add_plugin(self, name, module, plugin):
		if name in self.__plugins: raise Exception("Plugin %s with the name has already been added" % name)
		self.__plugins[name] = Plugin(name, module, plugin)
		return True

	def plugin(self, name):
		if name not in self.__plugins: raise Exception("Plugin %s named no" % name)
		return self.__plugins.get(name)

	def plugins(self):
		return self.__plugins.keys()

	# plugin: Plugin, events: List((event, args))
	def add_plugin_events(self, plugin, events):

		plugin.events = {}

		for event in events:
			plugin.events[event[0]] = Event(event[0], getattr(plugin.plugin, event[0]), event[1]) 

		return True

	def import_plugin(self, name):
		module = imp.load_source(name, '%s/%s.py'%(self.config.get('sm_plugin_dir'), name))
		plugin = module.setup(self)
		self.output("debug", str(plugin))
		return self.add_plugin(name, module, plugin)

	# plugin: Plugin
	def __req_plugins(self, plugin):
		req_plugins = getattr(plugin, PL_ATTR_REQUIRED_PLUGINS, [])
		plugins = self.plugins()
		for req_plugin in req_plugins:
			if req_plugin not in plugins: raise Exception("Plugins required for operation are required: %s" % ", ".join(req_plugins))

	def initialize_plugin(self, name):
		plugin = self.plugin(name)
		try:
			self.__req_plugins(plugin.plugin)
			events = simplefuncs.plugin_events(name)
			self.add_plugin_events(plugin, events)
			eEnable = plugin.events.get(PL_EVENT_ENABLE)
			if eEnable is not None:
				eEnable.method(*eEnable.args)

		except Exception, e:
			raise Exception("Plugin %s is not initialized: %s" % (name, e))

	def disable_plugin(self, name):
		plugin = self.plugin(name)
		try:
			eDisable = plugin.events.get(PL_EVENT_DISABLE)
			if eDisable is not None:
				eDisable.method(*eDisable.args)
		except Exception, e:
			raise Exception("Plugin %s is not shutdown: %s" % (name, e))

	def remove_plugin(self, name):
		plugin = self.plugin(name)
		del self.__plugins[name]
		return True

	def reload_plugin(self, name):
		self.disable_plugin(name)
		if self.remove_plugin(name):
			self.import_plugin(name)
			self.initialize_plugin(name)
			self.config.implement()

	def import_plugins(self):
		plugins = self.config.get('sm_plugins')
		logging.info("Importing plugins (%s)" % len(plugins))
		for plugin in plugins:
			try:
				self.import_plugin(plugin)
				logging.info("Plugin %s is imported" % (plugin))
			except Exception, e:
				self.output("error", "Plugin %s is not imported: %s", plugin, e)
				logging.exception(e)

	def initialize_plugins(self):
		plugins = self.plugins()
		logging.info("Initializing plugins (%s)" % len(plugins))
		for plugin in plugins:
			try:
				self.initialize_plugin(plugin)
				self.output("info", "Plugin %s is initialized", plugin)
			except Exception, e:
				logging.error(e, exc_info=True)

	def shutdown_plugins(self):
		plugins = self.plugins()
		logging.info("Shutdowning plugins (%s)" % len(plugins))
		for plugin in plugins:
			try:
				if self.disable_plugin(plugin): continue
				logging.info("Plugin %s is shutdown" % (plugin))
			except Exception, e:
				self.output("error", "Plugin %s is not shutdown: %s", plugin, e)
				logging.exception(e)

	def reload_plugins(self):
		plugins = self.plugins()
		logging.info("Reloading plugins (%s)" % len(plugins))
		for plugin in plugins:
			try:
				if self.reload_plugin(plugin): continue
				logging.info("Plugin %s is reloaded" % (plugin))
			except Exception, e:
				self.output("error", "Plugin %s is not reloaded: %s", plugin, e)
				logging.exception(e)

	def init(self):
		self.output("info", "\nA %s v%s by %s has started its work", self.name, self.version, self.developer)
		simplefuncs.add_event("onEnable")
		simplefuncs.add_event("onDisable")
		self.import_plugins()
		self.config.implement()
		self.initialize_plugins()

	def output(self, level, text, *args):
		text = text % args
		getattr(logging, level)(text)
		host.rcon_invoke("echo \"%s\"" % text.replace("\n", ""))

	def shutdown(self):
		self.output("info","\nA %s has completed its work", self.name)

	def update(self):
		pass

def logger(func):
	def wrapper(*argv, **kwargs):
		try:
			return func(*argv, **kwargs)
		except Exception, e:
			logging.critical(e, exc_info=True)
	return wrapper

simpleMod = SimpleMod()

@logger
def getInstance():
	return simpleMod

@logger
def init():
	simpleMod.init();

@logger
def shutdown():
	simpleMod.shutdown()

@logger
def update():
	simpleMod.update()