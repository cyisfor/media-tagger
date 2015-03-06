sub:
	PKG_CONFIG_PATH=/opt/ImageMagick/lib/pkgconfig $(MAKE) all

all: testImageInfo imageInfo

imageInfo: info.o record.o
	gcc -g -o $@ $^ `pkg-config --cflags --libs ImageMagick`

%.o: %.c
	gcc `pkg-config --cflags ImageMagick talloc` -g -c -o $@ $^


.PHONY: sub all

derp:
