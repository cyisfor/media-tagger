#include "ensure.h"
#include "make.h"
#include "message.h"
#include "filedb.h"

#include "record.h"

#include <bsd/unistd.h> // setproctitle

#include <sys/resource.h>
#include <stdlib.h>
#include <unistd.h> // read

extern char* environ[];

#define WORKER_IDLE 3600

int main(int argc, char** argv) {
  //struct rlimit memlimit = { 0x20000000, 0x20000000 };
  //setrlimit(RLIMIT_DATA,&memlimit);
  //setrlimit(RLIMIT_STACK,&memlimit);
  //setrlimit(RLIMIT_AS,&memlimit);
  setproctitle_init(argc,argv,environ);
  recordInit();
  filedb_top(".");
	record(INFO,"Started a lackey!");
  make_init();
	context* ctx = make_context();
	struct message m;
	alarm(WORKER_IDLE);

	for(;;) {
		ensure_eq(sizeof(m),read(STDIN_FILENO,&m,sizeof(m)));
		puts("boop");
		if(m.width > 0)
			make_resized(ctx,m.id,m.width);
		else
			make_thumbnail(ctx,m.id);

		write(STDOUT_FILENO,&m,1);

		alarm(WORKER_IDLE);
	}
}		

