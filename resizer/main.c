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
  filedb_top(".");
	record(INFO,"Started a lackey!");
  make_init();
	context* ctx = make_context();
	struct message m;
	for(;;) {
		assert(sizeof(m)==read(STDIN_FILENO,&m,sizeof(m)));
		puts("boop");
		if(m.resize)
			make_resized(ctx,m.resized.id,m.resized.width);
		else
			make_thumbnail(ctx,m.id);
	}
}		

