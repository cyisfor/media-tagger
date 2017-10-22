objects:=lib.o filedb.o make.o record.o
export PKG_CONFIG_PATH:=/custom/vips/lib/pkgconfig

PACKAGES=libuv vips
CFLAGS+=-g
CFLAGS+=-Ichild_waiter/
LDLIBS+=
CFLAGS+=`pkg-config --cflags $(PACKAGES)`
LDFLAGS+=`pkg-config --libs $(PACKAGES)` -lm

LINK=$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

all: lackey-bin lackey-master python.so

lackey-bin: main.o worker.o
	$(LINK) -lbsd

lackey-master: master.o record.o watch.o worker.o child_waiter/libwaiter.a
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

child_waiter/libwaiter.a: child_waiter/waiter.c| child_waiter
	$(MAKE) -C child_waiter libwaiter.a

child_waiter:
	git clone ~/code/child_waiter/ child_waiter
