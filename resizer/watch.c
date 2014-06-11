#include "filedb.h"

#include "record.h"

#include <stdio.h>
#include <string.h>
#include <stdlib.h> // NULL
#include <sys/types.h> // opendir etc
#include <dirent.h>
#include <assert.h>
#include <unistd.h> //pipe

#include <signal.h>

int pid = -1;
int p[2] = {};
char* incoming = NULL;

void on_dead(int sig) {
    signal(SIGCHLD,SIG_IGN);
    if(pid > 0) {
        record(INFO, "Killing child %d",pid);
        kill(pid,SIGTERM);
        waitpid(pid,NULL,0);
    }
    exit(0);
}

void restart(void) {
  if(pid > 0) return;
  pipe(p);
  pid = fork();
  if(pid==0) {
    close(p[0]);
    dup2(p[1],1);
    execlp("inotifywait","inotifywait","-q","-m","-c","-e","moved_to",incoming,NULL);
    exit(23);
  }
  record(INFO, "inotifywait has pid %d",pid);
  assert(pid>0);
  close(p[1]);
}

void sigchld(int signal) {
    waitpid(pid,NULL,0);
    pid = -1;
    exit(0);
}

void watch_run(void (*handle)(const char*,const char*)) {
  incoming = filedb_file("incoming",NULL);

  struct sigaction sa;
  sa.sa_handler = on_dead;
  sigemptyset(&sa.sa_mask);
  sa.sa_flags = SA_RESETHAND;
  assert(-1 != sigaction(SIGINT,&sa,NULL));
  assert(-1 != sigaction(SIGTERM,&sa,NULL));
  assert(-1 != sigaction(SIGQUIT,&sa,NULL));

  sa.sa_handler = sigchld;
  sa.sa_flags = 0;
  assert(-1 != sigaction(SIGCHLD,&sa,NULL));
  restart();

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
    if(len<0) 
        break;
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
