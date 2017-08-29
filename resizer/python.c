#include "message.h"

#include <fcntl.h> // O_*, open
#include <unistd.h> // write
#include <assert.h>

// a python ctypes stub for sending IDs as messages...

int init(void) {
	return open("incoming/queue",O_RDONLY|O_NONBLOCK);
}

void queue(int dest, uint32_t id, uint32_t width) {
	struct message m = {
		.id = id,
		.width = width
	};
	ssize_t amt = write(dest,&m,sizeof(m));
	if(amt == sizeof(m)) return;
	if(amt < 0) {
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
