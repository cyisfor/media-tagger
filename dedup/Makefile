CPPFLAGS=-g

all: create tomvtreehack

create: create.o
	g++ -g -o $@ $^ -lpHash -lpng

tomvtreehack: tomvtreehack.cpp
	g++ -g -I . -o $@ $^ -lpHash ./libmvptree.a
