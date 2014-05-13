objects:=lib.o watch.o filedb.o make.o main.o
PKG_CONFIG_PATH=/opt/ImageMagick/lib/pkgconfig

sub: 
	PKG_CONFIG_PATH=/opt/ImageMagick/lib/pkgconfig $(MAKE) lackey-bin

lackey-bin: $(objects)
	gcc `pkg-config --cflags ImageMagick` -o $@ $^ `pkg-config --libs ImageMagick` 

%.o: %.c
	gcc `pkg-config --cflags ImageMagick` -c -o $@ $^ 

clean:
	rm -f lackey-bin $(objects)
