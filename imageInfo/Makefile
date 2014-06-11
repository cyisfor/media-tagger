all: testImageInfo imageInfo

imageInfo: info.old.c record.o
	gcc -g -o $@ $^ `pkg-config --cflags --libs ImageMagick`
testImageInfo: info.c memory.c record.o
	gcc -g -o $@ $^ `pkg-config --cflags --libs ImageMagick`

record.o: record.c
	gcc -g -c -o $@ $^
