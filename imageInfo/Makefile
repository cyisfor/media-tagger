sub:
	PKG_CONFIG_PATH=/opt/ImageMagick/lib/pkgconfig $(MAKE) all

all: imageInfo textImageInfo

imageInfo: info.o record.o
	gcc -g -o $@ $^ `pkg-config --cflags --libs ImageMagick`

textImageInfo: info.c record.o
	gcc -DTEXT -g -o $@ $^ `pkg-config --cflags --libs ImageMagick`

%.o: %.c
	gcc `pkg-config --cflags ImageMagick talloc` -g -c -o $@ $^


.PHONY: sub all

derp:
