PACKAGES=libuv vips
objects:=lib.o filedb.o make.o record.o
export PKG_CONFIG_PATH:=/custom/vips/lib/pkgconfig

CFLAGS+=-g
CFLAGS+=-Ichild_waiter/
CFLAGS+=`pkg-config --cflags $(PACKAGES)`

LINK=$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

all: lackey-bin lackey-master python.so

O=$(patsubst %,o/%.o,$(N))

PACKAGES:=libuv vips
N:=main worker record make filedb lib
lackey-bin: $(O)
	$(LINK) -lbsd `pkg-config --libs $(PACKAGES)`


PACKAGES:=
N:=master record watch worker
lackey-master: $(O) child_waiter/libwaiter.a
	$(LINK)

N:=test_linebuf linebuf record
test_linebuf: $(O)
	$(LINK)

o/%.o: %.c | o
	gcc $(CFLAGS) -c -o $@ $^

o:
	mkdir $@

clean:
	rm -f lackey-bin lackey-master *.o
	rm -rf o/

test: test.o $(objects)
	$(LINK) -lbsd

python.so: python.c
	$(LINK) -shared -fPIC

child_waiter/libwaiter.a: child_waiter/waiter.c| child_waiter
	$(MAKE) -C child_waiter libwaiter.a

child_waiter:
	git clone ~/code/child_waiter/ child_waiter
