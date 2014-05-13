all: testImageInfo imageInfo

imageInfo: info.old.c
	gcc -g -o $@ $^ `pkg-config --cflags --libs ImageMagick`
testImageInfo: info.c memory.c
	gcc -g -o $@ $^ `pkg-config --cflags --libs ImageMagick`
