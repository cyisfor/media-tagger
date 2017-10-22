#include "worker.h"

#define LITLEN(a) a,(sizeof(a)-1)

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h> // _un


#include <stdlib.h> // abort
#include <stdio.h> // perror
#include <string.h> // memcpy


#define WORKERADDR "\0/image-resizer/master"

int start_working(bool is_master) {
	int sock = socket(AF_UNIX, SOCK_DGRAM, 0);
	struct sockaddr_un addr = {
		.sun_family = AF_UNIX,
	};
	memcpy(addr.sun_path,LITLEN(WORKERADDR));
	if(is_master) {
		if(bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0)
			return -1;
		if(listen(sock, 5) < 0) {
			perror("listen master");
			abort();
		}
	} else {
		if(connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0)
			return -1;
	}
	return sock;
}
