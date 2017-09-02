#define _GNU_SOURCE // O_PATH, openat
#include "message.h"

#include <fcntl.h> // O_*, open
#include <unistd.h> // write
#include <assert.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h> // abort
#include <limits.h> // PATH_MAX
#include <string.h> // memcpy


// a python ctypes stub for sending IDs as messages...

static const char reopen_incoming[PATH_MAX];
static int q = -1;

static void reinit() {
	int loc = open(reopen_incoming,O_DIRECTORY|O_PATH);
	assert(loc >= 0);
	q = openat(loc,"incoming",O_WRONLY|O_NONBLOCK);
	assert(q > 0);
	close(loc);
}

void init(const char* incoming, int len) {
	memcpy(reopen_incoming, incoming, len);
	reinit();
}

int queue(uint32_t id, uint32_t width) {
	struct message m = {
		.id = id,
		.width = width
	};
	printf("queueing %d\n",q);
	int doit(void) {
		ssize_t amt = write(q,&m,sizeof(m));
		if(amt == sizeof(m)) return 0;
		if(amt < 0) {
			if(errno == EAGAIN) return 1;
			if(errno == EPIPE) {
				init(reopen_incoming);
				return doit();
			}
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
	return doit();
}
