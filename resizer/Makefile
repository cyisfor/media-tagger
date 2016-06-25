objects:=lib.o watch.o filedb.o make.o main.o record.o
export PKG_CONFIG_PATH:=/custom/vips/lib/pkgconfig

PACKAGES=libuv vips
CFLAGS+=-g
CFLAGS+=`pkg-config --cflags $(PACKAGES)`
LDFLAGS+=`pkg-config --libs $(PACKAGES)`

all: lackey-bin lackey-master

lackey-bin: $(objects)
	gcc $(CFLAGS) -o $@ $^ $(LDFLAGS) -lbsd

lackey-master: master.o record.o
	gcc $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	gcc $(FLAGS) `pkg-config --cflags vips` -c -o $@ $^ 

clean:
	rm -f lackey-bin $(objects)
