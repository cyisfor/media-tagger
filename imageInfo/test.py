import filedb

from main import get,Error
print(get("test.png"))
print(get("test.png"))
try:
    print(get("lollydoodle"))
except Error: pass

print(get(filedb.mediaPath(0x6a2e6)))
