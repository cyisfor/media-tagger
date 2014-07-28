#include <unistd.h>
#include <string.h> // strrchr
#include <stdlib.h> // malloc
#include <stdio.h>
#include <errno.h>
#include <signal.h>

#include "record.h"

#define NUM 4
#define WORKER_LIFETIME 3600 // like an hour idk

int workers[NUM];

const char* lackey = NULL;
const char* filedb = NULL;

int startLackey(void) {    
    int pid = fork();
    if(pid == 0) {
        execl(lackey,"lackey",filedb,NULL);
        exit(23);
    }
    return pid;
}

void onchild(int signal) {}

void onalarm(int signal) {
    // randomly kill a worker, to keep them fresh 
    // b/c memory leaks in ImageMagick
    static int ctr = 0;
    kill(workers[ctr],SIGTERM);
    ctr = (ctr + 1)%NUM;
    alarm(WORKER_LIFETIME/NUM); 
    // it'll cycle through them all in a lifetime
    // visit each once a lifetime
}

int main(int argc, char** argv) {
    srand(time(NULL));
    recordInit();
    char* buf; 
    ssize_t amt;
    char* lastslash = strrchr(argv[0],'/');
    if(lastslash == NULL) {
        lackey = "./lackey-bin";
    } else {
        amt = lastslash - argv[0] + 1;
        char* buf = malloc(amt + sizeof("lackey-bin"));
        memcpy(buf,argv[0],amt);
        memcpy(buf+amt,"lackey-bin",sizeof("lackey-bin"));
        buf[amt+sizeof("lackey-bin")] = '\0';
        lackey = buf;
        record(INFO, "lackey '%s'",lackey);
    }
    
    {
        amt = strlen(getenv("HOME"));
        buf = malloc(amt + sizeof("/art/filedb"));
        memcpy(buf,getenv("HOME"),amt);
        memcpy(buf+amt,"/art/filedb",sizeof("/art/filedb"));
        filedb = buf;
        record(INFO, "filedb '%s'",filedb);
    }

    setenv("LD_LIBRARY_PATH","/opt/ImageMagick/lib",1);
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = onchild;
    sigaction(SIGCHLD,&sa,NULL);

    sa.sa_handler = onalarm;
    sigaction(SIGALRM,&sa,NULL);
    alarm(WORKER_LIFETIME);

    int i = 0;
    for(;i<NUM;++i) {
        workers[i] = startLackey();
    }
    for(;;) {
        pause();
        if(errno != EINTR) break;
        int kid = wait(NULL);
        sleep(1);
        record(INFO,"restarting for pid %d",kid);
        for(i=0;i<NUM;++i) {
            if(workers[i] == kid) {
                puts("found it!");
                workers[i] = startLackey();
                break;
            }
        }
    }
    return 0;
}