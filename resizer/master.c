#define _GNU_SOURCE // ppoll
#include "ensure.h"
#include "record.h"
#include "watch.h"
#include "message.h"

#include <sys/signalfd.h>

#include <sys/inotify.h>
#include <poll.h>

#include <assert.h>

#include <stdbool.h>

#include <unistd.h>
#include <string.h> // strrchr
#include <stdlib.h> // malloc
#include <stdio.h>
#include <errno.h>
#include <signal.h>
#include <fcntl.h> // locking
#include <error.h>
#include <sys/wait.h>
#include <time.h>
#include <stdlib.h> // null

#define NUM 4
#define WORKER_LIFETIME 3600 * 1000 // like an hour idk
#define RESTART_DELAY 1000

int queue;

typedef unsigned char byte;

int *workers = NULL;
byte numworkers = 0;

void started_worker(int pid) {
	workers = realloc(workers,(++numworkers)*sizeof(*workers));
	workers[numworkers-1] = pid;
	assert(numworkers < 12);
}

void reap_workers(void) {
	for(;;) {
		int status;
		int pid = waitpid(-1,&status,WNOHANG);
		if(pid < 0) {
			if(errno == EINTR) continue;
			if(errno != EAGAIN && errno != ECHILD) {
				perror("reap");
				abort();
			}
			break;
		}

		if(WIFSIGNALED(status) && SIGALRM==WTERMSIG(status)) {
			record(INFO, "worker %d retiring",pid);
		} else {
			record(INFO,"worker %d died (exit %d sig %d)",
						 pid,
						 WEXITSTATUS(status),
						 WTERMSIG(status));
		}
		int which;
		for(which=0;which<numworkers;++which) {
			if(workers[which] == pid) {
				memmove(workers+which,
								workers+which+1,
								--numworkers - which);
			}
		}
		// okay if never finds the pid, may have already been removed
	}
}

void stop_a_worker(void) {
	/*
	byte which;
	int res = getrandom(&which,sizeof(which),0);
	assert(sizeof(which) == res);
	which = which % numworkers;
	*/

	static byte which = 0;
	// note this could kill a worker in the middle of thumbnail generation
	// but this will also kill a worker stuck in the middle of thumbnail generation
	record(INFO,"killing worker %d",which);

	// should we not remove it proactively?
	int pid = workers[which];
	if(which == numworkers-1) {
		--numworkers;
	} else {
		memmove(workers+which,
						workers+which+1,
						--numworkers - which);
	}
	// it'll cycle through them all in a lifetime
	// visit each once a lifetime
	which = (which + 1)%numworkers;
	// just... assume it dies I guess.
	kill(pid,SIGTERM);
}

char lackey[PATH_MAX];


void start_worker(void) {
	record(INFO,"starting lackey #%d",numworkers);
	const char* args[] = {"cgexec","-g","memory:/image_manipulation",
//												"valgrind",
									lackey,NULL};
	int pid = fork();
	if(pid == 0) {
		chdir("..");
		dup2(queue,0);
		close(queue);
		ensure0(fcntl(0,F_SETFL, fcntl(0,F_GETFL) & ~O_NONBLOCK));

		execvp("cgexec",(void*)args);
		abort();
	}
	started_worker(pid);
}

static void dolock(void) {
  int fd = open("/tmp/lackey-master.lock", O_WRONLY|O_CREAT,0600);
  if(fd < 0) error(1,0,"Lock wouldn't open.");
  struct flock lock = {
    .l_type = F_WRLCK,
  };
  if(-1 != fcntl(fd,F_SETLK,&lock)) return;
  switch(errno) {
  case EACCES:
  case EAGAIN:
    exit(2);
  default:
    error(3,errno,"Couldn't set a lock.");
  };
}

/* inotify keeps missing files, and we don't really need a persistent queue.
	 just re-queue thumbnails on demand if the computer dies.

	 new plan:

	 1 named pipe
	 fixed size message struct
	 various p's write messages to pipe
	 lackeys read messages from pipe
	 if pipe is full, send message to master, it may (MAY) spawn more lackeys
	 then block


	 1 named pipe master listens on
	 when it gets a byte, someone's complaining the pipe is full.
	 if not max lackeys, spawn a new one.
	 always make sure at least 1 lackey is there to drain the pipe
	 setup message pipe to be stdin on lackey
*/

int main(int argc, char** argv) {
	sigset_t mysigs;
  dolock();

	srand(time(NULL));
	recordInit();
	ssize_t amt;
	realpath(argv[0],lackey);
	char* lastslash = strrchr(lackey,'/');
	if(lastslash == NULL) {
		realpath("./lackey-bin",lackey);
	} else {
		// take the real path of us, and convert the end to lackey-bin
		amt = lastslash - lackey + 1;
		record(INFO,"realp %s",lackey+amt);
		memcpy(lackey+amt,"lackey-bin",sizeof("lackey-bin"));
	}
	record(INFO, "lackey '%s'",lackey);

	if(0!=chdir("/home/.local/filedb/incoming")) abort();
	mkfifo("queue",0644);
	mkfifo("queuefull",0644);

	// fcntl cannot remove nonblocking from pipes, so... just hang master until there's
	// something to do.
	for(;;) {
		// we're opening our pipe for writing, so that it doesn't go into an EOF spin loop
		// when there are no more writers
		queue = open("queue",O_RDWR); // dup2 this to stdin for lackeys, otherwise ignore
		if(queue<0) {
			ensure_eq(errno,EINTR);
		} else {
			break;
		}
	}
	int queuefull = open("queuefull",O_RDWR|O_NONBLOCK);
	assert(queuefull >= 0);

	enum { SIGNALS, QUEUEFULL };

	/* block the signals we care about
		 this does NOT ignore them, but queues them up
		 and interrupts stuff like ppoll (which reenables getting hit by those signals atomically)
		 then we can read info off the signalfd at our leisure, with no signal handler jammed in-between
		 an if(numworkers == 0) and start_worker();
	*/
	
	sigemptyset(&mysigs);
	sigaddset(&mysigs,SIGCHLD);
	int res = sigprocmask(SIG_BLOCK, &mysigs, NULL);
	assert(res == 0);
	
	// could technically use queue for this, since never read from it...?
	int signals = signalfd(-1,&mysigs,SFD_NONBLOCK);
	assert(signals >= 0);

	struct pollfd pfd[] = {
		[SIGNALS] = {
			.fd = signals,
			.events = POLLIN
		},
		[QUEUEFULL] = {
			.fd = queuefull,
			.events = POLLIN
		}
	};

	start_worker();

	for(;;) {
		int res = ppoll((struct pollfd*)&pfd, 2, NULL, &mysigs);
		if(res < 0) {
			if(errno == EINTR) continue;
			perror("poll");
			abort();
		}
		errno = 0;
		if(res == 0) {
			// timed out while waiting for events?
			continue;
		}
		if(pfd[QUEUEFULL].revents && POLLIN) {
			char buf[0x1000];
			size_t pokes = 0;
			for(;;) {
				ssize_t amt = read(queuefull,&buf,sizeof(buf));
				if(amt == 0) {
					perror("EOF on queuefull...");
					break;
				}
				if(amt < 0) {
					if(errno == EAGAIN) break;
					perror("read queue full");
					abort();
				}
				pokes += amt;
			}

			// stop a random worker in case it froze?
			if(numworkers >= NUM) {
				stop_a_worker();
			}

			/* the more pokes, the more stuff is blocking on this (hopefully)
				 so make sure between cur and NUM lackeys are running, with more pokes closer to NUM

				 TODO: benchmark this to determine how many pokes.
			*/
#define min(a,b) ({ typeof(a) a1 = (a); typeof(b) b1 = (b); a1 < b1 ? a1 : b1; })
			int target;
			if(pokes > 10) {
				target = min(numworkers+3,NUM);
			} else if(pokes > 3) {
				target = min(numworkers+2,NUM);
			} else {
				target = min(numworkers+1,NUM);
			}
			int i;
			for(i=numworkers;i<target;++i) {
				start_worker();
			}
		} else if(pfd[SIGNALS].revents) {
			// something died
			// TODO: stop repeatedly trying to make thumbnails if it keeps dying
			struct signalfd_siginfo info;
			for(;;) {
				ssize_t amt = read(signals,&info,sizeof(info));
				if(amt < 0) {
					if(errno == EAGAIN) break;
					if(errno==EINTR) continue;
					perror("signals");
					abort();
				}
				assert(amt == sizeof(info));
				assert(info.ssi_signo == SIGCHLD);
				// don't care about ssi_pid since multiple kids could have exited
				reap_workers();
				if(numworkers == 0) {
					start_worker();
				}
			}
		}
	}
}
