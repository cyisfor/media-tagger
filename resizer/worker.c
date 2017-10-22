#include "worker.h"

#define LITLEN(a) a,(sizeof(a)-1)

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h> // _un

#include <fcntl.h> // O_*
#include <stdlib.h> // abort
#include <stdio.h> // perror
#include <string.h> // memcpy


#define WORKERADDR "\0/image-resizer/master"

int start_working(bool is_master) {
	int sock = socket(AF_UNIX, SOCK_STREAM, 0);
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
		fcntl(sock, F_SETFL, fcntl(sock, F_GETFL) | O_NONBLOCK);	
	} else {
		if(connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0)
			return -1;
	}
	return sock;
}
