#define _GNU_SOURCE // ppoll
#include "ensure.h"
#include "record.h"
#include "watch.h"
#include "message.h"
#include "timeop.h"

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

static sigset_t mysigs;

#define MAXWORKERS 5

struct pollfd pfd[MAXWORKERS+2] = {};
size_t numpfd = 2; // = 2 + numworkers... always?





int launch_worker(int in, int out) {
	const char* args[] = {"cgexec","-g","memory:/image_manipulation",
//												"valgrind",
									lackey,NULL};
	int pid = fork();
	if(pid == 0) {
		ensure_eq(0,sigprocmask(SIG_UNBLOCK, &mysigs, NULL));
		ensure0(fcntl(in,F_SETFL, fcntl(in,F_GETFL) & ~(O_CLOEXEC | O_NONBLOCK)));
		ensure0(fcntl(out,F_SETFL, fcntl(out,F_GETFL) & ~(O_CLOEXEC | O_NONBLOCK)));

		if(in != 3) {
			dup2(in,3);
			close(in);
		}
		if(out != 4) {
			dup2(out,4);
			close(out);
		}
		// XXX: is this needed?
		execvp("cgexec",(void*)args);
		abort();
	}
	return pid;
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

enum status { DEAD, DOOMED, IDLE, BUSY };
Time DOOM_DELAY = {
	tv_sec: 0,
	tv_nsec: NSECPERSEC / 2 // half a second
};

struct worker {
	enum status status;
	int pid;
	int in[2];
	int out[2];
	uint32_t current;
	struct timespec expiration;
};

struct worker workers[MAXWORKERS];
size_t numworkers = 0;

#define WORKER_LIFETIME 60


void set_expiration(size_t which) {
	// set on creation, reset every time a worker goes idle
	getnowspec(&workers[which].expiration);
	workers[which].expiration.tv_sec += WORKER_LIFETIME;
}

void start_worker(size_t which) {
	pipe2(workers[which].in,O_NONBLOCK);
	pipe2(workers[which].out,O_NONBLOCK);
	
	workers[which].status = IDLE;
	record(INFO,"starting lackey #%d",which);
	workers[which].pid = launch_worker(workers[which].in[0],
																		 workers[which].out[1]);
	close(workers[which].in[0]);
	close(workers[which].out[1]);

	pfd[which+2].fd = workers[which].out[0];
	pfd[which+2].events = POLLIN;

	set_expiration(which);
	++numworkers;
}

void reap_workers(void) {
	for(;;) {
		int status;
		int pid = waitpid(-1,&status,WNOHANG);
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
		for(which=0;which<numworkers;++which) {
			if(workers[which].pid == pid) {
				--numworkers;
				close(workers[which].in[1]);
				close(workers[which].out[0]);
				workers[which].status = DEAD;
			}
		}
		// okay if never finds the pid, may have already been removed
	}
}

void kill_worker(int which) {
	kill(workers[which].pid,SIGKILL);
	reap_workers();
	ensure_eq(workers[which].status,DEAD);
	pfd[which+2].events = 0;
}

void stop_worker(int which) {
	workers[which].status = DOOMED;
	kill(workers[which].pid,SIGTERM);
	reap_workers();
	if(workers[which].status == DEAD) return;
	workers[which].expiration = timeadd(getnow(),DOOM_DELAY);
}

size_t get_worker(size_t off) {
	// get a worker
	// off, so we don't check worker 0 a million times
	int which = 0;
	for(which=0;which<MAXWORKERS;++which) {
		size_t derp = (which+off)%MAXWORKERS;
		switch(workers[derp].status) {
		case DEAD:
			continue;
		case IDLE:
			workers[derp].status = BUSY;
			pfd[derp+2].events = POLLIN;
			return derp;
		};
	}

	if(numworkers == MAXWORKERS) {
		for(which=0;which<MAXWORKERS;++which) {
			if(workers[which].status == DOOMED) {
				/*
					if 995 ns left (expiration - now) and doom delay is 1000ns
					1000 - 995 < 50, so wait a teensy bit longer please
				*/
				Time diff = timediff(DOOM_DELAY,
														 timediff(workers[which].expiration,
																			getnow()));
				if(diff.tv_nsec > 50) {
					kill_worker(which);
					start_worker(which);
					return which;
				}
			}
		}
		return MAXWORKERS;
	}
	
	for(which=0;which<MAXWORKERS;++which) {
		if(workers[which].status != DEAD) continue;
		start_worker(which);
		return which;
	}
	return numworkers++;
}

void send_message(size_t which, const struct message m) {
	record(INFO,"Sending %d to %d",m.id,workers[which].pid);
	ssize_t amt = write(workers[which].in[1], &m, sizeof(m));
	if(amt == 0) {
		stop_worker(which);
		return;
	}
	if(amt < 0) {
		switch(errno) {
		case EPIPE:
			return send_message(get_worker(which), m);
		};
		perror("write");
		abort();
	}
	ensure_eq(amt, sizeof(m));
	workers[which].current = m.id; // eh
}

void derp() {}

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

	sigemptyset(&mysigs);
	// workers will die, we need to handle
//	signal(SIGCHLD,derp);
	sigaddset(&mysigs,SIGCHLD);
//	signal(SIGPIPE,derp);
	sigaddset(&mysigs,SIGPIPE);
	int res = sigprocmask(SIG_BLOCK, &mysigs, NULL);
	assert(res == 0);
	
	int signals = signalfd(-1,&mysigs,SFD_NONBLOCK);
	assert(signals >= 0);

	enum { SIGNALS, INCOMING };

	pfd[SIGNALS].fd = signals;
	pfd[SIGNALS].events = POLLIN;
	pfd[INCOMING].fd = incoming;
	pfd[INCOMING].events = POLLIN;

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
	
	void drain_incoming(void) {
		struct message m;
		size_t worker = 0;
		for(;;) {
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
			worker = get_worker(worker);
			if(worker == MAXWORKERS) {
				pfd[INCOMING].events = 0;
				break;
			}
			send_message(worker,m);
		}
	}
	
	// calculate timeout by worker with soonest expiration - now.

	struct timespec timeout;
	bool forever = true;
	size_t soonest_worker = 0;
	if(numworkers > 0) {
		size_t i;
		timeout = workers[0].expiration;
		for(i=1;i<numworkers;++i) {
			if(time2units(timediff(timeout, workers[i].expiration)) > 0) {
				// this worker expires sooner
				timeout = workers[i].expiration;
				soonest_worker = i;
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

	forever = false;
	timeout.tv_sec = 3;
	timeout.tv_nsec = 0;
	
	for(;;) {
		int res = ppoll((struct pollfd*)&pfd,
										2+numworkers,
										&timeout,
										&mysigs);
		if(res < 0) {
			if(errno == EINTR) continue;
			perror("poll");
			abort();
		}
		errno = 0;
		if(res == 0 & numworkers > 0) {
			// timed out while waiting for events?
			if(workers[soonest_worker].status == DOOMED) {
				kill_worker(soonest_worker);
			}
#if 0
			else {
				stop_worker(soonest_worker);
			}
#endif
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
				case SIGPIPE:
					continue; // eh
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
			char c;
			void drain(void) {
				for(;;) {
					ssize_t amt = read(workers[which].out[0],&c,1);
					if(amt == 0) {
						return;
					} else if(amt < 0) {
						switch(errno) {
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
				if(pfd[which+2].fd == workers[which].out[0]) {
					drain();
					workers[which].status = IDLE;
					pfd[which+2].events = 0;
				}
			}
		}
	}
}
