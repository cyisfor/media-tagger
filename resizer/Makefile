objects:=lib.o filedb.o make.o record.o
export PKG_CONFIG_PATH:=/custom/vips/lib/pkgconfig

PACKAGES=libuv vips
CFLAGS+=-g
CFLAGS+=`pkg-config --cflags $(PACKAGES)`
LDFLAGS+=`pkg-config --libs $(PACKAGES)` -lm

LINK=$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

all: lackey-bin lackey-master

lackey-bin: main.o $(objects)
	$(LINK) -lbsd

lackey-master: master.o record.o watch.o
	$(LINK)

test_linebuf: test_linebuf.o linebuf.o record.o
	$(LINK)

%.o: %.c
	gcc $(CFLAGS) -c -o $@ $^ 

clean:
	rm -f lackey-bin lackey-master *.o

test: test.o $(objects)
	$(LINK) -lbsd

python.so: python.c
	$(LINK) -shared -fPIC
