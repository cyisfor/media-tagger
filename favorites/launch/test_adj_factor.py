def one(progress,total):
	factor = total / 0xFFFF
	return progress//factor, (total // factor), factor

print(one(1000000,1000000))
print(one(0,1000000))
print(one(1000000-1,1000000))
print(one(1000000+1,1000000))

print(one(65535,65536))
