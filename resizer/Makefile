objects:=lib.o watch.o filedb.o make.o main.o record.o
export PKG_CONFIG_PATH:=/custom/vips/lib/pkgconfig

FLAGS=-g

all: lackey-bin lackey-master

lackey-bin: $(objects)
	gcc $(FLAGS) `pkg-config --cflags vips` -o $@ $^ `pkg-config --libs vips` -lbsd

lackey-master: master.o record.o
	gcc $(FLAGS) `pkg-config --cflags libuv` -o $@ $^ `pkg-config --libs libuv`

master.o: FLAGS+=`pkg-config --cflags libuv`

%.o: %.c
	gcc $(FLAGS) `pkg-config --cflags vips` -c -o $@ $^ 

clean:
	rm -f lackey-bin $(objects)
