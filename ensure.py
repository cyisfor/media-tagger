# because assert screws up side effects.

def ensure(t):
	if not t:
		raise RuntimeError("assertion failed")
