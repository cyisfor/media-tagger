#define _GNU_SOURCE // O_PATH, openat
#include "message.h"

#include <fcntl.h> // O_*, open
#include <unistd.h> // write
#include <assert.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h> // abort


// a python ctypes stub for sending IDs as messages...

int init(const char* incoming) {
	int loc = open(incoming,O_DIRECTORY|O_PATH);
	assert(loc >= 0);
	int ret = openat(loc,"incoming",O_WRONLY|O_NONBLOCK);
	assert(ret > 0);
	close(loc);
	return ret;
}

int queue(int q, uint32_t id, uint32_t width) {
	struct message m = {
		.id = id,
		.width = width
	};
	ssize_t amt = write(q,&m,sizeof(m));
	if(amt == sizeof(m)) return 0;
	if(amt < 0) {
		if(errno == EAGAIN) return 1;
		fprintf(stderr,"%d\n",q);
		perror("oops");
		return 2;
	}
	if(amt == 0) {
		perror("whu?");
		return 3;
	}
	fprintf(stderr,"Ummm %d %d\n",amt,sizeof(m));
	return 4;
}
