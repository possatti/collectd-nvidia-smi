# Fake file, just for testing a little bit of the plugin outside of collectd.

def register_config(*args, **kwargs):
	pass

def register_read(*args, **kwargs):
	pass

def info(s):
	print('info:', s, file=sys.stderr)

def error(s):
	print('error:', s, file=sys.stderr)
