#define _GNU_SOURCE // ppoll
#include "worker.h"
#include "ensure.h"
#include "record.h"
#include "message.h"
#include "timeop.h"
#include "waiter.h"

#include <sys/stat.h> // mkfifo
#include <sys/socket.h> // accept

#include <limits.h> // PATH_MAX

#include <poll.h>

#include <assert.h>

#include <stdbool.h>

#include <unistd.h>
#include <string.h> // strrchr
#include <stdlib.h> // malloc, realpath
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

enum { INCOMING, ACCEPTING };

static
int launch_worker(int master) {
	const char* args[] = {"cgexec","-g","memory:/image_manipulation",
//												"valgrind",
									lackey,NULL};
	int pid = waiter_fork();
	if(pid != 0) return pid;

	if(master != 3) {
		dup2(master,3);
		close(master);
	}
	setenv("usethree","1",1);

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

enum status { IDLE, BUSY, DOOMED };

Time DOOM_DELAY = {
	tv_sec: 0,
	tv_nsec: NSECPERSEC / 2 // half a second
};

struct worker {
	enum status status;
	uint32_t current;
	pid_t pid;
	struct timespec expiration;
};

struct worker* workers = NULL;
size_t numworkers = 0;

#define WORKER_LIFETIME 60

void worker_connected(int sock) {
	workers = realloc(workers,sizeof(*workers)*++numworkers);
	workers[numworkers-1].status = IDLE;
	workers[numworkers-1].pid = -1;
	record(INFO,"starting lackey #%d %d",numworkers-1,sock);

	pfd = realloc(pfd,sizeof(*pfd)*(numworkers+2));
	pfd[numworkers+1].fd = sock;
	pfd[numworkers+1].events = POLLIN;
	//pfd[numworkers+1].revents = POLLOUT; meh
	pfd[numworkers+1].revents = 0;
}

void remove_worker(int which) {
	for(;which<numworkers-1;++which) {
		PFD(which) = (&(PFD(which)))[1];
		// XXX: close() kill() waitpid()?
		workers[which] = workers[which+1];
	}
	--numworkers; // don't bother with shrinking realloc
}

static
void reap_workers(void) {
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
			record(INFO, "sub %d retiring",pid);
		} else {
			record(INFO,"sub %d died (exit %d sig %d)",
						 pid,
						 WEXITSTATUS(status),
						 WTERMSIG(status));
		}
		int which;
		for(which=0;which<numworkers;++which) {
			if(workers[which].pid == pid) {
				close(PFD(which).fd);
				remove_worker(which);
				break;
			}
		}
		// okay if never finds the pid, may have already been removed
	}
}

static
bool wait_for_accept(void) {
	// accept the connection
	// wait up to 0.5s
	struct timespec timeout = {0, 500000000};
	for(;;) {
		int res = waiter_wait(&pfd[ACCEPTING],1,&timeout);
		if(res < 0) {
			if(errno == EINTR) {
				reap_workers();
				continue;
			}
			if(errno == EAGAIN) {
				// uh... how?
				continue;
			}
			perror("get_worker wait");
			abort();
		}
		return res == 1;
		// don't waste time hanging in this mini-poll waiting for accept
	}
}

static
bool start_worker(void) {
	if(numworkers >= MAXWORKERS) return false;
	// returns true if ACCEPTING is ready
	int pair[2];
	ensure0(socketpair(AF_UNIX,SOCK_STREAM,0,pair));
	worker_connected(pair[0]);
	getnowspec(&workers[numworkers-1].expiration);
	workers[numworkers-1].expiration.tv_sec += WORKER_LIFETIME;
	workers[numworkers-1].pid = launch_worker(pair[1]);
	close(pair[1]);
}

void kill_worker(int which) {
	kill(workers[which].pid,SIGKILL);
	close(PFD(which).fd);
	remove_worker(which);
	reap_workers();
}

void stop_worker(int which) {
	workers[which].status = DOOMED;
	workers[which].expiration = timeadd(getnow(),DOOM_DELAY);
	kill(workers[which].pid,SIGTERM);
	reap_workers();
}

static
bool accept_workers(void) {
	bool dirty = false;
	for(;;) {
		int sock = accept(pfd[ACCEPTING].fd, NULL, NULL);
		if(sock < 0) {
			if(errno == EAGAIN) return dirty;
			perror("accept");
			abort();
		}
		dirty = true;
		fcntl(sock, F_SETFL, fcntl(sock, F_GETFL) | O_NONBLOCK);
		worker_connected(sock);
	}
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

	/* no idle found, try starting some workers */
	if(numworkers < MAXWORKERS) {
		// add a worker to the end
		if(start_worker()) {
			return numworkers-1;
		}
	} else {
		reap_workers();
		for(which=0;which<numworkers;++which) {
			if(workers[which].status == DOOMED) {
				/*
					if 995 ns left (expiration - now) and doom delay is 1000ns
					1000 - 995 < 50, so wait a teensy bit longer please
				*/
				Time diff = timediff(DOOM_DELAY,
														 timediff(workers[which].expiration,
																			getnow()));
				if(diff.tv_nsec > 50) {
					// waited too long, kill the thing.
					kill_worker(which);
					if(start_worker()) {
						return numworkers-1;
					}
				}
			}
		}
	}
	if(wait_for_accept()) {
		if(accept_workers()) {
			return get_worker();
		}
	}
	// have to wait until the new worker connects
	errno = EAGAIN; // eh
	return -1;
}

bool send_message(size_t which, const struct message m) {
	record(INFO,"Sending %d to %d",m.id,which);
	ssize_t amt = write(PFD(which).fd, &m, sizeof(m));
	if(amt == 0) {
		return false;
	}
	if(amt < 0) {
		switch(errno) {
		case EPIPE:
		case EBADF:
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

	assert(0 == numworkers);
	pfd = malloc(sizeof(*pfd)*2);

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

	struct {
		struct message m;
		bool ready;
	} pending = {};

	bool resend_pending(void) {
		if(!pending.ready) return false;
		for(;;) {
			size_t worker = get_worker();
			if(worker == -1) {
				// clog us up until we can get a worker
				printf("can't find a worker to send %d\n", pending.m.id);
				return false;
			}
			if(send_message(worker,pending.m)) {
				puts("sent message");
				pfd[INCOMING].events = POLLIN;
				pending.ready = false;
				return true;
			}
			perror("send message failed...");
			workers[worker].status = BUSY;
			// then try getting another worker.
		}
	}

	void drain_incoming(void) {
		record(DEBUG, "drain incoming");		
		if(pending.ready) {
			resend_pending();
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
			printf("%d pending\n",pending.m.id);
			pending.ready = true;
			pfd[INCOMING].events = 0;
			if(!resend_pending()) break;
		}
	}
	
	// calculate timeout by worker with soonest expiration - now.

	struct timespec timeout;
	bool forever = true;
	size_t soonest_worker = 0;
	if(numworkers > 0) {
		size_t i;
		for(i=1;i<numworkers;++i) {
			if(workers[i].pid != -1) {
				forever = false;
				timeout = workers[i].expiration;
				for(++i;i<numworkers;++i) {
					if(workers[i].pid == -1) continue;
					if(time2units(timediff(timeout, workers[i].expiration)) > 0) {
						// this worker expires sooner
						timeout = workers[i].expiration;
						soonest_worker = i;
					}
				}
			}
		}
		if(!forever) {
			Time now = getnow();
			timeout = timediff(timeout,now);
		}
	}

	for(;;) {
		int res = waiter_wait(pfd,
													numworkers+2,
													forever ? NULL : &timeout);
		if(res < 0) {
			if(errno == EINTR) {
				reap_workers();
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
		if(res == 0 & numworkers > 0) {
			// timed out while waiting for events?
			if(workers[soonest_worker].status == DOOMED) {
				// took too long to die, so kill it
				kill_worker(soonest_worker);
			} else {
				stop_worker(soonest_worker);
			}
			continue;
		}
		if(pfd[ACCEPTING].revents && POLLIN) {
			accept_workers();
			drain_incoming();
		}
		if(pfd[INCOMING].revents && POLLIN) {
			drain_incoming();
		}
		// check who went idle
		char c;
		void drain(int which) {
			for(;;) {
				ssize_t amt = read(PFD(which).fd,&c,1);
				if(amt == 0) {
					return;
				} else if(amt < 0) {
					switch(errno) {
					case ECONNRESET:
					case EBADF:
						close(PFD(which).fd);
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
		int check(int which) {
			if(PFD(which).revents == 0) {
				// nothing here
			} else if(PFD(which).revents & POLLNVAL) {
				printf("invalid socket at %d %d %d %d\n",
							 which,
							 PFD(which).fd,
							 PFD(which).revents,
							 workers[which].pid);
				poll(NULL, 0, 1000);
				drain(which);
				reap_workers();
				remove_worker(which);
				return which;
				//--which; // ++ in the next iteration
			} else if(PFD(which).revents & POLLHUP) {
				printf("worker %d(%d) hung up\n",PFD(which).fd, which);
				drain(which);
				close(PFD(which).fd);
				if(workers[which].pid != -1) {
					stop_worker(which); // bad idea?
				}
				remove_worker(which);
				reap_workers();
				return which;
			} else if(PFD(which).revents & POLLIN) {
				printf("worker %d(%d) went idle\n",PFD(which).fd, which);
				drain(which);
				workers[which].status = IDLE;
				drain_incoming();
			} else {
				printf("weird revent? %x\n",PFD(which).revents);
			}
			return which+1;
		}
		int which=0;
		while(which<numworkers) {
			which = check(which);
		}
		if(pending.ready) {
			if(start_worker())
				check(numworkers-1);
		}
	}
}
