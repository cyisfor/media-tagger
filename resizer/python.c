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

static char reopen_incoming[PATH_MAX];
static int q = -1;

static int reinit() {
	int loc = open(reopen_incoming,O_DIRECTORY|O_PATH);
	if(loc < 0) {
		printf("bad loc %s\n",reopen_incoming);
		perror("foo");
		abort();
	}
	q = openat(loc,"incoming",O_WRONLY|O_NONBLOCK);
	if(q < 0) {
		printf("oops %s\n",reopen_incoming);
		close(loc);
		sleep(1);
		return -1;
	}
	close(loc);
	return 0;
}

int init(const char* incoming, int len) {
	memcpy(reopen_incoming, incoming, len);
	return reinit();
}

int queue(uint32_t id, uint32_t width) {
	struct message m = {
		.id = id,
		.width = width
	};
	printf("queueing %x\n",id);
	int doit(void) {
		ssize_t amt = write(q,&m,sizeof(m));
		if(amt == sizeof(m)) return 0;
		if(amt < 0) {
			switch(errno) {
			case EAGAIN:
			case EINTR:
				return 1;
			case EPIPE:
			case EBADF:
				reinit();
				return doit();
			default:
				fprintf(stderr,"%d\n",q);
				perror("oops");
				return 2;
			};
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
