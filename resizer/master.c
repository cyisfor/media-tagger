#define _GNU_SOURCE // ppoll
#include "ensure.h"
#include "record.h"
#include "watch.h"
#include "message.h"

#include <sys/signalfd.h>
#include <sys/eventfd.h>

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

//#define WORKER_LIFETIME 3600 * 1000 // like an hour idk
#define RESTART_DELAY 1000

typedef unsigned char byte;

char lackey[PATH_MAX];

int start_worker(int efd) {
	const char* args[] = {"cgexec","-g","memory:/image_manipulation",
//												"valgrind",
									lackey,NULL};
	int pid = fork();
	if(pid == 0) {
		chdir("..");
		dup2(efd,0);
		close(efd);
		// XXX: is this needed?
		ensure0(fcntl(0,F_SETFL, fcntl(0,F_GETFL) & ~O_NONBLOCK));

		execvp("cgexec",(void*)args);
		abort();
	}
	return pid;
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

	 this works, but...
	 * can't tell which lackey's doing what thumb
	 * can't tell when a lackey's finished with a thumb, to handle timeouts in master
	 * can't really figure out how to ramp up as requests come in, since can't tell when
	   lackeys are busy.

	 so instead... 1 named pipe that master listens to, that messages are written on.
	 each worker has an eventfd. master writes messages to that eventfd (64 bits), then
	 marks the worker as busy. The worker writes a response, which master polls for, then
	 sets the worker to not busy.

	 Before reading from the pipe (once it's readable) if all workers are busy, add a new one,
	 unless you're at max workers. Then disable polling on the pipe and chill. If an eventfd
	 isn't readable in long enough, kill that worker, and set its error flag. if timeout again,
	 kill it with KILL.
	 
	 when a worker dies, memmove the others together, so the top of the array is marked as
	 the dead part. Can we reuse the eventfds? Mark as -1 initially, then when a dead worker's
	 not -1, use that eventfd in the fork.
*/

enum status { DEAD, DOOMED, IDLE, BUSY };

struct worker {
	enum status status;
	int pid;
	int efd;
	uint32_t current;
	time_t expiration;
};
#define MAXWORKERS 4 // # CPUs?

struct worker workers[MAXWORKERS];
size_t numworkers = 0;

#define WORKER_LIFETIME 60

void set_expiration(size_t which) {
	// set on creation, reset every time a worker goes idle
	struct timespec now;
	clock_gettime(CLOCK_MONOTONIC, &now);
	workers[which].expiration = now.tv_sec + WORKER_LIFETIME;
}

size_t get_worker(size_t off) {
	// get a worker
	// off, so we don't check worker 0 a million times
	int which = 0;
	for(which=0;which<numworkers;++which) {
		size_t derp = (which+off)%numworkers;
		if(workers[derp].status == IDLE) {
			workers[derp].status = BUSY;
			return derp;
		}
	}
	// need a new worker
	if(numworkers + 1 == MAXWORKERS) {
		return MAXWORKERS;
	}
	if(workers[numworkers].efd < 0) {
		workers[numworkers].efd = eventfd(0,0);
	}
	record(INFO,"starting lackey #%d",numworkers);
	workers[numworkers].pid = start_worker(workers[numworkers].efd);
	set_expiration(numworkers);
	return numworkers++;
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
			if(workers[which].pid == pid) {
				if(which == numworkers) {
					// no problem
				} else {
					memmove(workers+which,
									workers+which+1,
									sizeof(struct worker) * (--numworkers - which));
				}
				workers[numworkers--].status = DEAD; // just in case...
			}
		}
		// okay if never finds the pid, may have already been removed
	}
}

void send_message(size_t which, const struct message m) {
	ssize_t amt = write(workers[which].efd, &m, sizeof(m));
	if(amt == 0) {
		// full, but IDLE was set?
		workers[which].status = DOOMED;
		kill(worker[which].pid,SIGTERM);
	}
	ensure_eq(amt, sizeof(m));
}

int main(int argc, char** argv) {
	ensure_eq(argc,2);
	
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

	if(0!=chdir(argv[1])) abort(); // ehhhh

	mkfifo("incoming",0644); // not a directory anymore

	// we're opening our pipe for writing, so that it doesn't go into an EOF spin loop
	// when there are no more writers
	int incoming = open("incoming",O_RDWR|O_NONBLOCK);

	void drain_incoming(void) {
		struct message m;
		size_t worker = 0;
		for(;;) {
			worker = get_worker(worker);
			if(worker == MAXWORKERS) {
				pfd[INCOMING].events = 0;
				break;
			} 
			ssize_t amt = read(incoming,&m,sizeof(m));
			if(amt == 0) {
				perror("EOF on queuefull...");
				break;
			}
			if(amt < 0) {
				if(errno == EAGAIN) break;
				perror("incoming fail");
				abort();
			}
			send_message(worker,m);
		}
	}

	/* block the signals we care about
		 this does NOT ignore them, but queues them up
		 and interrupts stuff like ppoll (which reenables getting hit by those signals atomically)
		 then we can read info off the signalfd at our leisure, with no signal handler jammed in-between
		 an if(numworkers == 0) and start_worker();
	*/
	
	sigemptyset(&mysigs);
	// workers will die, we need to handle
	sigaddset(&mysigs,SIGCHLD);
	int res = sigprocmask(SIG_BLOCK, &mysigs, NULL);
	assert(res == 0);
	
	int signals = signalfd(-1,&mysigs,SFD_NONBLOCK);
	assert(signals >= 0);

	enum { SIGNALS, INCOMING };

	struct pollfd pfd[NUM+2] = {
		[SIGNALS] = {
			.fd = signals,
			.events = POLLIN
		},
		[INCOMING] = {
			.fd = incoming,
			.events = POLLIN
		}
	};
	size_t numpfd = 2; // = 2 + numworkers... always?

	// calculate timeout by worker with soonest expiration - now.

	struct timespec timeout;
	bool forever = true;
	size_t soonest_worker;
	if(numworkers > 0) {
		timeout.tv_sec = workers[0].due;
		timeout.tv_nsec = 0;
		for(i=1;i<numworkers;++i) {
			if(timeout.tv_sec > workers[i].expiration) {
				timeout.tv_sec = workers[i].expiration;
				soonest_worker = i;
			}
		}
		forever = false;
		struct timespec now;
		clock_gettime(CLOCK_MONOTONIC,&now);
		if(timeout.tv_sec >= now.tv_sec) {
			timeout.tv_sec -= now.tv_sec;
		} else {
			timeout.tv_sec = 0;
		}
	}
	
	for(;;) {
		int res = ppoll((struct pollfd*)&pfd,
										numpfd,
										forever ? NULL : &timeout,
										&mysigs);
		if(res < 0) {
			if(errno == EINTR) continue;
			perror("poll");
			abort();
		}
		errno = 0;
		if(res == 0) {
			// timed out while waiting for events?
			if(worker[soonest_worker].status == DOOMED) {
				kill(worker[soonest_worker].pid,SIGKILL);
			} else {
				worker[soonest_worker].status = DOOMED;
				kill(worker[soonest_worker].pid,SIGTERM);
			}
			continue;
		}
		if(pfd[INCOMING].revents && POLLIN) {
			drain_incoming();
		} else if(pfd[SIGNALS].revents && POLLIN) {
			// something died
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
				switch(info.ssi_signo) {
				case SIGCHLD:
					// don't care about ssi_pid since multiple kids could have exited
					// we can take more from the pipe now.
					reap_workers();
					pfd[INCOMING].events = POLLIN;
					drain_incoming();
					break;
				default:
					perror("huh?");
					abort();
				};
			}
		} else {
			// someone went idle!
			int which;
			for(which=0;which<numworkers;++which) {
				if(pfd[which+2].fd == workers[which].efd) {
					char c;
					ssize_t amt = read(workers[which].efd,&c,1);
					ensure_eq(amt,1);
					workers[which].status = IDLE;
					break;
				}
			}
		}
	}
}
