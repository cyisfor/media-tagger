objects:=lib.o watch.o filedb.o make.o main.o record.o
PKG_CONFIG_PATH=/opt/ImageMagick/lib/pkgconfig

FLAGS=-g

sub: 
	PKG_CONFIG_PATH=/opt/ImageMagick/lib/pkgconfig $(MAKE) all

all: lackey-bin lackey-master

lackey-bin: $(objects)
	gcc $(FLAGS) `pkg-config --cflags ImageMagick` -o $@ $^ `pkg-config --libs ImageMagick` -lbsd

lackey-master: master.o record.o
	gcc $(FLAGS) -o $@ $^

%.o: %.c
	gcc $(FLAGS) `pkg-config --cflags ImageMagick` -c -o $@ $^ 

clean:
	rm -f lackey-bin $(objects)
