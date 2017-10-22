#include "worker.h"
#define WORKERADDR "\0/image-resizer/master"

int start_working(bool is_master) {
	int sock = socket(AF_UNIX, SOCK_DGRAM, 0);
	struct sockaddr_un addr = {
		.sun_family = AF_UNIX,
	};
	memcpy(addr.sun_path,LITLEN(ERRPATH));
	if(capturing) {
		if(bind(sock, &addr, sizeof(addr)) < 0)
			return -1;
		failif(listen(sock, 5),"listen capture");
	} else {
		if(connect(sock, &addr, sizeof(addr)) < 0)
			return -1;
	}
	return sock;
}

