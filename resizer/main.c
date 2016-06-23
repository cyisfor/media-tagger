#include "make.h"
#include "watch.h"
#include "filedb.h"

#include "record.h"

#include <bsd/unistd.h> // setproctitle

#include <sys/resource.h>
#include <stdlib.h>
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
  char* temp = filedb_file("temp",NULL);
  setenv("MAGICK_TEMPORARY_PATH",temp,1);
  free(temp);
  make_init();
  watch_run(make_create);
  return 0;
}
