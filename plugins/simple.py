import logging
from simplefuncs import event

class Simple(object):

	name = "Simple"
	version = "0.0.1"
	developers = ""

	def __str__(self):
		return "%s v%s by %s" % (self.name, self.version, self.developers)

	def __init__(self, sm):
		self.sm = sm

	@event()
	def onEnable(self):
		logging.info("Hi Simp!")

	@event()
	def onDisable(self):
		logging.info("Bye Simp!")

def setup(simplemod):
	return Simple(simplemod)