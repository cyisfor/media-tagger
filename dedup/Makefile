CPPFLAGS=-g

all: create tomvtreehack

create: create.o
	g++ -g -o $@ $^ -lpHash

tomvtreehack: tomvtreehack.cpp
	g++ -g -I . -o $@ $^ -lpHash ./libmvptree.a
