#define _GNU_SOURCE // O_PATH, openat
#include "message.h"

#include <fcntl.h> // O_*, open
#include <unistd.h> // write
#include <assert.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h> // abort


// a python ctypes stub for sending IDs as messages...

int q,queuefull;

void init(const char* incoming) {
	int loc = open(incoming,O_DIRECTORY|O_PATH);
	assert(loc >= 0);
	q = openat(loc,"queue",O_WRONLY|O_NONBLOCK);
	queuefull = openat(loc,"queuefull",O_WRONLY);
	close(loc);
}

int queue(uint32_t id, uint32_t width) {
	struct message m = {
		.id = id,
		.width = width
	};
	ssize_t amt = write(q,&m,sizeof(m));
	if(amt == sizeof(m)) return 1;
	if(amt < 0) {
		if(errno == EAGAIN) {
			char c = 0;
			write(queuefull,&c,1);
			return 0;
		}
		fprintf(stderr,"%d\n",q);
		perror("oops");
		abort();
	}
	if(amt == 0) {
		perror("whu?");
		abort();
	}
	fprintf(stderr,"Ummm %d %d\n",amt,sizeof(m));
	abort();
}
