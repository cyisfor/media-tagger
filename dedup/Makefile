PKG_CONFIG_PATH=/custom/pHash/lib/pkgconfig
export PKG_CONFIG_PATH
CPPFLAGS=-g `pkg-config --cflags pHash`
LDFLAGS=-g `pkg-config --libs pHash`
all: create tomvtreehack

create: create.o
	g++ -g -o $@ $^ -lpHash -lpng $(LDFLAGS)

tomvtreehack: tomvtreehack.cpp ./mvptree/libmvptree.a
	g++ -g -I . $(CPPFLAGS) -o $@ tomvtreehack.cpp -lpHash ./mvptree/libmvptree.a $(LDFLAGS)

./mvptree/libmvptree.a:
	$(MAKE) -C mvptree $@
