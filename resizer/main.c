#include "make.h"
#include "message.h"
#include "filedb.h"

#include "record.h"

#include <bsd/unistd.h> // setproctitle

#include <sys/resource.h>
#include <stdlib.h>
#include <unistd.h> // read

#include <assert.h>

extern char* environ[];

int main(int argc, char** argv) {
  //struct rlimit memlimit = { 0x20000000, 0x20000000 };
  //setrlimit(RLIMIT_DATA,&memlimit);
  //setrlimit(RLIMIT_STACK,&memlimit);
  //setrlimit(RLIMIT_AS,&memlimit);
  setproctitle_init(argc,argv,environ);
  recordInit();
  record(ERROR,"error");
  record(WARN,"warning");
  record(INFO,"info");
  record(DEBUG,"debug");
  assert(argc==2);
  filedb_top(argv[1]);
	chdir(argv[1]);
  make_init();
	context* ctx = make_context();
	struct message m;
	for(;;) {
		assert(sizeof(m)==read(STDIN_FILENO,&m,sizeof(m)));
		if(m.resize)
			make_resized(ctx,m.resized.id,m.resized.width);
		else
			make_thumbnail(ctx,m.id);
	}
}		

