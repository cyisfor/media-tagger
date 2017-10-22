#define _GNU_SOURCE // ppoll
#include "worker.h"
#include "ensure.h"
#include "record.h"
#include "watch.h"
#include "message.h"
#include "timeop.h"
#include "waiter.h"

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

#define MAXWORKERS 5

struct pollfd* pfd = NULL;
// pfd[0] is for incoming requests
// pfd[1] is for accepting lackey connections
// pfd[x+2] => worker[x]
#define PFD(which) pfd[which+2]

static
int launch_worker(void) {
	const char* args[] = {"cgexec","-g","memory:/image_manipulation",
//												"valgrind",
									lackey,NULL};
	int pid = waiter_fork();
	if(pid != 0) return pid;
	
	// XXX: is this needed?
	execvp("cgexec",(void*)args);
	abort();
}

static void dolock(void) {
  int fd = open("temp/.lackey-master.lock", O_WRONLY|O_CREAT,0600);
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

enum status { IDLE, BUSY };

Time DOOM_DELAY = {
	tv_sec: 0,
	tv_nsec: NSECPERSEC / 2 // half a second
};

struct worker {
	enum status status;
	int sock;
	uint32_t current;
};

struct worker* workers = NULL;
size_t numworkers = 0;

#define WORKER_LIFETIME 60

void worker_connected(int sock) {
	workers = realloc(workers,sizeof(*workers)*++numworkers);
	workers[numworkers-1].status = IDLE;
	record(INFO,"starting lackey #%d",numworkers-1);

	pfd = realloc(pfd,sizeof(*pfd)*(numworkers+2));
	pfd[numworkers+1].fd = sock;
	pfd[numworkers+1].events = POLLIN;
}

void remove_worker(int which) {
	int i;
	for(i=which;i<numworkers-1;++i) {
		PFD(which) = (&(PFD(which)))[1];
		workers[which] = workers[which+1];
	}
	--numpfd;
	--numworkers; // don't bother with shrinking realloc
}

struct sub {
	bool doomed;
	pid_t pid;
	Time expiration;
}	subs[MAXWORKERS];
int nsubs = 0;

static
void start_sub(void) {
	if(nsubs == MAXWORKERS) return;
	subs[nsubs].doomed = false;
	getnowspec(&subs[nsubs].expiration);
	subs[nsubs].expiration.tv_sec += WORKER_LIFETIME;
	subs[nsubs].pid = launch_worker();
}

static
void reap_subs(void) {
	waiter_drain();
	for(;;) {
		int status;
		int pid = waiter_next(&status);
		if(pid == 0) return;
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
		for(which=0;which<nsubs;++which) {
			if(subs[which].pid == pid) {
				for(;which<nsubs;++which) {
					subs[which] = subs[which+1];
				}
				--nsubs;
				break;
			}
		}
		// okay if never finds the pid, may have already been removed
	}
}

void kill_sub(int which) {
	kill(subs[which].pid,SIGKILL);
	reap_subs();
}

void stop_sub(int which) {
	subs[which].doomed = true;
	subs[which].expiration = timeadd(getnow(),DOOM_DELAY);
	kill(subs[which].pid,SIGTERM);
	reap_subs();
}

size_t get_worker(void) {
	// get a worker
	// off, so we don't check worker 0 a million times
	static size_t off = -1;
	++off;
	int which;
	for(which=0;which<numworkers;++which) {
		size_t derp = (which+off)%numworkers;
		switch(workers[derp].status) {
		case IDLE:
			workers[derp].status = BUSY;
			PFD(derp).events = POLLIN;
			return derp;
		};
	}

	errno = EAGAIN; // eh
	
	/* no idle found, try starting some subs */
	if(numworkers < MAXWORKERS) {
		// add a worker to the end
		start_sub();
		return -1;
	}

	reap_subs();
	for(which=0;which<nsubs;++which) {
		if(subs[which].status == DOOMED) {
			/*
				if 995 ns left (expiration - now) and doom delay is 1000ns
				1000 - 995 < 50, so wait a teensy bit longer please
			*/
			Time diff = timediff(DOOM_DELAY,
													 timediff(workers[which].expiration,
																		getnow()));
			if(diff.tv_nsec > 50) {
				// waited too long, kill the thing.
				kill_sub(which);
				start_sub();
			}
		}
	}
	// have to wait for the worker to connect now...
	return -1;
}

bool send_message(size_t which, const struct message m) {
	record(INFO,"Sending %d to %d",m.id,workers[which].pid);
	ssize_t amt = write(workers[which].in[1], &m, sizeof(m));
	if(amt == 0) {
		return false;
	}
	if(amt < 0) {
		switch(errno) {
		case EPIPE:
			return false;
		};
		perror("write");
		abort();
	}
	ensure_eq(amt, sizeof(m));
	workers[which].current = m.id; // eh
	return true;
}

int main(int argc, char** argv) {
	ensure_eq(argc,2);
	recordInit();

	init_timeop();
	
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

	ensure_eq(0,chdir(argv[1])); // ehhhh
	
  dolock();

	mkfifo("incoming",0644); // not a directory anymore

	// we're opening our pipe for writing, so that it doesn't go into an EOF spin loop
	// when there are no more writers
	int incoming = open("incoming",O_RDWR|O_NONBLOCK);

	/* block the signals we care about
		 this does NOT ignore them, but queues them up
		 and interrupts stuff like ppoll (which reenables getting hit by those signals atomically)
		 then we can read info off the signalfd at our leisure, with no signal handler jammed in-between
		 an if(numworkers == 0) and start_worker();
	*/

	waiter_setup();

	enum { INCOMING, ACCEPTING };

	numpfd = 2;
	pfd = malloc(sizeof(pfd)*numpfd);

	pfd[INCOMING].fd = incoming;
	pfd[INCOMING].events = POLLIN;

	pfd[ACCEPTING].fd = start_working(true);
	pfd[ACCEPTING].events = POLLIN;

	void clear_incoming(void) {
		char buf[512];
		for(;;) {
			ssize_t amt = read(incoming,buf,512);
			if(amt <= 0) {
				ensure_eq(errno,EAGAIN);
				break;
			}
		}
		record(INFO,"Incoming fifo unclogged");
	}
	clear_incoming();

	void accept_workers(void) {
		for(;;) {
			int sock = accept(pfd[ACCEPTING].fd, NULL, NULL);
			if(sock < 0) {
				if(errno == EAGAIN) return;
				perror("accept");
			}
			worker_connected(sock);
		}
	}		

	struct {
		struct message m;
		bool is;
	} pending = {};
	
	void drain_incoming(void) {
		record(DEBUG, "drain incoming");		
		if(pending.is) {
			size_t worker = get_worker();
			if(worker == -1) return;
			if(!send_message(worker,pending.m)) {
				perror("send message failed...");
				return;
			}
			pending.is = false;
			return;
		}
		for(;;) {
			ssize_t amt = read(incoming,&pending.m,sizeof(pending.m));
			if(amt == 0) {
				perror("EOF on queuefull...");
				break;
			}
			if(amt < 0) {
				if(errno == EAGAIN) return;
				perror("incoming fail");
				abort();
			}
			for(;;) {
				size_t worker = get_worker();
				if(worker == -1) {
					pfd[INCOMING].events = 0;
					// clog us up until we can get a worker
					pending.is = true;
					return;
				}
				if(send_message(worker,pending.m)) {
					pending.is = false;
					return;
				}
				perror("send message failed...");
				workers[worker].status = BUSY;
				// then try getting another worker.
			}
		}
	}
	
	// calculate timeout by worker with soonest expiration - now.

	struct timespec timeout;
	bool forever = true;
	size_t soonest_sub = 0;
	if(nsubs > 0) {
		size_t i;
		timeout = subs[0].expiration;
		for(i=1;i<nsubs;++i) {
			if(time2units(timediff(timeout, subs[i].expiration)) > 0) {
				// this worker expires sooner
				timeout = subs[i].expiration;
				soonest_sub = i;
			}
		}
		forever = false;
		Time now = getnow();
		if(timeout.tv_sec >= now.tv_sec) {
			timeout.tv_sec -= now.tv_sec;
		} else {
			timeout.tv_sec = 0;
		}
	}

	for(;;) {
		int res = waiter_wait((struct pollfd*)&pfd,
													1+numworkers,
													forever ? NULL : &timeout);
		if(res < 0) {
			if(errno == EINTR) {
				reap_subs();
				pfd[INCOMING].events = POLLIN;
				continue;
			} else if(errno == EAGAIN) {
				// huh?
				continue;
			}
			perror("poll");
			abort();
		}
		errno = 0;
		if(res == 0 & nsubs > 0) {
			// timed out while waiting for events?
			if(subs[soonest_sub].doomed) {
				// took too long to die, so kill it
				kill_sub(soonest_sub);
			} else {
				stop_sub(soonest_sub);
			}
			continue;
		}
		if(pfd[INCOMING].revents && POLLIN) {
			drain_incoming();
		} else if(pfd[ACCEPTING].revents && POLLIN) {
			accept_workers();
		} else {
			// someone went idle!
			int which;
			char c;
			void drain(void) {
				for(;;) {
					ssize_t amt = read(workers[which].sock,&c,1);
					if(amt == 0) {
						return;
					} else if(amt < 0) {
						switch(errno) {
						case EBADF:
							close(workers[which].sock);
							return;
						case EAGAIN:
							return;
						case EINTR:
							continue;
						default:
							perror("huh?");
							abort();
						};
					} else {
						//ensure_eq(amt,1);
					}
				}
			}
			for(which=0;which<numworkers;++which) {
				if(PFD(which).fd == workers[which].sock) {
					if(PFD(which).revents == 0) {
						// nothing here
					} else if(PFD(which).revents && POLLNVAL) {
						printf("invalid socket at %d %d\n",which,workers[which].sock);
						drain();
						reap_subs();
						remove_worker(which);
						--which; // ++ in the next iteration
					} else if(PFD(which).revents && POLLHUP) {
						drain();
						close(workers[which].sock);
						reap_subs();
						remove_worker(which);
						--which; // ++ in the etc
					} else if(PFD(which).revents && POLLIN) {
						drain();
						workers[which].status = IDLE;
					} else {
						printf("weird revent? %x\n",PFD(which).revents);
					}
				}
			}
		}
	}
}
