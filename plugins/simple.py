import logging

class Simple(object):

	name = "Simple"
	version = "0.0.1"
	developers = ""

	def __str__(self):
		return "%s v%s by %s" % (self.name, self.version, self.developers)

	def __init__(self, sm):
		self.sm = sm

	def init(self):
		logging.info("Hi Simp")

def setup(simplemod):
	return Simple(simplemod)