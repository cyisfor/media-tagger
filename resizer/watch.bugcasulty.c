#include "filedb.h"

#include <inotifytools/inotifytools.h>
#include <inotifytools/inotify.h>
#include <stdlib.h> // NULL
#include <sys/types.h> // opendir etc
#include <dirent.h>
#include <assert.h>

void watch_run(void (*handle)(const char*,const char*)) {
  inotifytools_initialize();
  char* incoming = filedb_file("incoming",NULL);
  if(-1==inotifytools_watch_file(incoming,IN_MOVED_TO|IN_ONLYDIR)) {
    free(incoming);
    perror("could not add watch");
    exit(3);
  }

  DIR* d = opendir(incoming);
  for(;;) {
    struct dirent* ent = readdir(d);
    if(!ent) break;
    handle(incoming,ent->d_name);
  }
  closedir(d);

  char buf[sizeof(struct inotify_event)+0x400];
  for(;;) {
    struct inotify_event* event = inotifytools_next_event(0);
    handle(incoming,event->name);
  }
}
