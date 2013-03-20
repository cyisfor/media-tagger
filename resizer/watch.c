#include "filedb.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h> // NULL
#include <sys/types.h> // opendir etc
#include <dirent.h>
#include <assert.h>
#include <unistd.h> //pipe

void watch_run(void (*handle)(const char*,const char*)) {
  char* incoming = filedb_file("incoming",NULL);
  int p[2] = {};
  pipe(p);
  int pid = fork();
  if(pid==0) {
    close(p[0]);
    dup2(p[1],1);
    execlp("inotifywait","inotifywait","-m","-c","-e","moved_to",incoming,NULL);
    exit(23);
  }
  assert(pid>0);

  close(p[1]);

  DIR* d = opendir(incoming);

  for(;;) {
    struct dirent* ent = readdir(d);
    if(!ent) break;
    handle(incoming,ent->d_name);
  }
  closedir(d);

  char* line = NULL;
  size_t n = 0;
  FILE* src = fdopen(p[0],"r");
  assert(src);
  for(;;) {
    ssize_t len = getline(&line,&n,src);
    if(len<0) break;
    assert(line);
    assert(len < n);
    line[len-1] = '\0';
    char* path = strchr(line,',');
    if(path==NULL) continue;
    path = strchr(path+1,',');
    if(path==NULL) continue;
    handle(incoming,path+1);
  }
}
