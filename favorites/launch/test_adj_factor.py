def one(progress,total):
	factor = total // 0xFFFF + 1
	return progress//factor, (total // factor - 1), factor

print(one(1000000,1000000))
print(one(0,1000000))
print(one(1000000-1,1000000))
print(one(1000000+1,1000000))

print(one(65536,65536))
