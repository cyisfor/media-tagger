#include "message.h"

#include <fcntl.h> // O_*, open
#include <unistd.h> // write
#include <assert.h>
#include <stdio.h>

// a python ctypes stub for sending IDs as messages...

int init(void) {
	return open("incoming/queue",O_WRONLY|O_NONBLOCK);
	return open("incoming/queuefull",O_WRONLY);
}

void queue(int dest, uint32_t id, uint32_t width) {
	struct message m = {
		.id = id,
		.width = width
	};
	ssize_t amt = write(dest,&m,sizeof(m));
	if(amt == sizeof(m)) return;
	if(amt < 0) {
		fprintf(stderr,"%d\n",dest);
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
