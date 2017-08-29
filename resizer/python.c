#include "message.h"

#include <fcntl.h> // O_*, open
#include <unistd.h> // write
#include <assert.h>

// a python ctypes stub for sending IDs as messages...

int python_resize_init(void) {
	return open("incoming/queue",O_RDONLY|O_NONBLOCK);
}

void python_queue_resize(int dest, uint32_t id, uint32_t width) {
	struct message m = {
		.id = id,
		.width = width
	};
	ssize_t amt = write(dest,&m,sizeof(m));
	assert(amt == sizeof(m));
}
