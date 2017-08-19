#define _GNU_SOURCE // ppoll
#include "record.h"
#include "watch.h"
#include "message.h"

#include <sys/signalfd.h>

#include <sys/inotify.h>
#include <poll.h>

#include <assert.h>

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

int queue[2];

typedef unsigned char byte;

int *workers = NULL;
byte numworkers = 0;

void started_worker(int pid) {
	workers = realloc(workers,(++numworkers)*sizeof(*workers));
	workers[numworkers-1] = pid;
	assert(numworkers < 12);
}

struct diedmsg {
	int pid;
	int status;
};

int died[2];

void reap_workers(void) {
	for(;;) {
		int status;
		int pid = waitpid(-1,&status,WNOHANG);
		if(pid < 0) {
			if(errno == EINTR) continue;
			if(errno != EAGAIN) {
				perror("reap");
				abort();
			}
			break;
		}

		record(INFO,"worker %d died (exit %d sig %d)",
					 pid,
					 WEXITSTATUS(status),
					 WTERMSIG(status));
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
	memmove(workers+which,
					workers+which+1,
					--numworkers - which);
	// it'll cycle through them all in a lifetime
	// visit each once a lifetime
	which = (which + 1)%numworkers;
	// just... assume it dies I guess.
	kill(pid,SIGTERM);
}

char lackey[PATH_MAX];


void start_worker(void) {
	const char* args[] = {"cgexec","-g","memory:/image_manipulation",
//												"valgrind",
									lackey,NULL};
	int pid = fork();
	if(pid == 0) {
		chdir("..");
		dup2(queue[0],0);
		close(queue[0]);
		close(queue[1]);
		execvp("cgexec",(void*)args);
		abort();
	}
	started_worker(pid);
}

static void dolock(void) {
  int fd = open("/tmp/lackey-masterderp.lock", O_WRONLY|O_CREAT,0600);
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

static bool file_changed(struct message* message, const char* filename) {
	if(filename[0] == '\0' || filename[0] == '.') return false;

	uint32_t ident = strtol(filename,NULL,0x10);
	assert(ident > 0 && ident < (1<<31)); // can bump 1<<31 up in message.h l8r

	int fd = open(filename,O_RDONLY);
	if(fd == -1) {
		// got deleted somehow
		return false;
	}
	// regardless of success, if fail this'll just repeatedly fail
  // so delete it anyway
  unlink(filename);

	char buf[0x100];
	ssize_t len = read(fd,buf,0x100);

	message->id = ident;
	if(len) {
		buf[len] = '\0';
		uint32_t width = strtol(buf, NULL, 0x10);
		if(width > 0) {
			record(INFO,"Got width %x, sending resize request",width);
			message->resize = true;
			message->resized.width = width;
			return true;
		}
	} else {
		message->resize = false;
		return true;
	}
	return false;
}

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

	chdir("/home/.local/filedb/incoming");

	pipe(queue);
	fcntl(queue[1],F_SETFL, fcntl(queue[1],F_GETFL) | O_NONBLOCK);
	int watcher = inotify_init1(IN_NONBLOCK);

	enum { SIGNALS, WATCHERQUEUE };

	sigemptyset(&mysigs);
	sigaddset(&mysigs,SIGCHLD);
	int res = sigprocmask(SIG_BLOCK, &mysigs, NULL);
	assert(res == 0);
	
	// could technically use queue[1] for this, since never read from it...?
	int signals = signalfd(-1,&mysigs,SFD_NONBLOCK);
	assert(signals >= 0);

	struct pollfd pfd[] = {
		[SIGNALS] = {
			.fd = signals,
			.events = POLLIN
		},
		[WATCHERQUEUE] = {
			.fd = watcher,
			.events = POLLIN
		}
	};

	inotify_add_watch(watcher,".",IN_MOVED_TO|IN_CLOSE_WRITE);

	/* block the signals we care about
		 this does NOT ignore them, but queues them up
		 and interrupts stuff like ppoll (which reenables getting hit by those signals atomically)
		 then we can read info off the signalfd at our leisure, with no signal handler jammed in-between
		 an if(numworkers == 0) and start_worker();
	*/
		 
	// shouldn't need a queue of these... I hope
	// either poll watcher, or poll queue, if going in or out. always poll signalfd.
	bool watching = true;

#define NMESS 1024
	struct message messages[NMESS]; // keep a ring buffer I guess...
	int smess = 0;
	int emess = 0;

	int send_message(void) {
		record(INFO,"sending req for %d to child",messages[smess].id);
		return write(queue[1],&messages[smess],sizeof(messages[smess]));
	}

	struct timespec last;
	clock_gettime(CLOCK_MONOTONIC,&last);

	struct timespec timeout;
	void worker_lifetime(void) {
		struct timespec now;
		timeout.tv_sec = WORKER_LIFETIME / 1000;
		timeout.tv_nsec = 1000000*(WORKER_LIFETIME%1000);
		// but reduce the timeout by the difference between last and now.
		// timeout = timeout - (now - last) watch out for signed error / overflow error
		clock_gettime(CLOCK_MONOTONIC,&now);
		timeout.tv_sec -= now.tv_sec - last.tv_sec;
		if(timeout.tv_nsec + last.tv_nsec >= now.tv_nsec) {
			timeout.tv_nsec = timeout.tv_nsec + last.tv_nsec - now.tv_nsec;
		} else {
			if(timeout.tv_sec == 0) {
				timeout.tv_nsec = 0;
			} else {
				--timeout.tv_sec;
				timeout.tv_nsec = 1000000000 - now.tv_nsec + timeout.tv_nsec + last.tv_nsec;
			}				
		}
	}
	for(;;) {
		// ramp up timeout the more workers we have hanging out there
		if(watching || numworkers > 3) worker_lifetime();
		else if(numworkers == 1) timeout.tv_sec = 100;
		else if(numworkers == 2) timeout.tv_sec = 500;
		else if(numworkers == 3) timeout.tv_sec = 3000;

		int res = ppoll((struct pollfd*)&pfd, 2, &timeout,&mysigs);
		if(res < 0) {
			if(errno == EINTR) continue;
			perror("poll");
			abort();
		}
		if(res == 0) {
			// timed out... we should kill a worker

			assert(pfd[2].events);
			if(numworkers >= NUM) {
				stop_a_worker();
			}
			start_worker();
			clock_gettime(CLOCK_MONOTONIC,&last);
			continue;
		}
		if(pfd[WATCHERQUEUE].revents) {
			// file changed, or need write message
			if(watching) {
				struct {
					struct inotify_event ev;
					char name[NAME_MAX];
				} ev;
				watching = false;
				pfd[WATCHERQUEUE].fd = queue[1];
				pfd[WATCHERQUEUE].events = POLLOUT;

				for(;;) {
					ssize_t amt = read(watcher,&ev,sizeof(ev));
					if(amt < 0) {
						if(errno == EAGAIN) break;
						perror("file changed");
						assert(errno == EINTR);
					} else {
						record(INFO,"file changed %s",ev.name);
						assert(amt >= sizeof(ev.ev));
						assert(amt <= sizeof(ev));
						if((emess+1)%NMESS == smess) {
							record(ERROR, "queue full!");
							abort();
						}
						if(file_changed(&messages[emess], ev.name)) {
							if(numworkers == 0)
								start_worker(); // start at least one
							int res = send_message();
							if(res < 0) {
								// just trying it out
								assert(errno == EINTR || errno == EAGAIN);
								// definitely queue it since we can't write right now
								emess = (emess + 1) % NMESS;
							} else {
								assert(res == sizeof(messages[smess]));
								// don't bother queuing it.
								watching = true;
								pfd[WATCHERQUEUE].fd = watcher;
								pfd[WATCHERQUEUE].events = POLLIN;
							}
						}
					}
				}
			} else {
				int res = send_message();
				assert(res == sizeof(messages[smess]));
				smess = (smess + 1) % NMESS;
				if(smess == emess) {
					// queue empty
					// now pull more file changes
					pfd[WATCHERQUEUE].fd = watcher;
					pfd[WATCHERQUEUE].events = POLLIN;
					watching = true;
				}
			}
		} else if(pfd[SIGNALS].revents) {
			record(INFO, "signal?");
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
				assert(info.ssi_signo == SIGCHLD);
				// don't care about ssi_pid since multiple kids could have exited
				reap_workers();
			}
		}
	}
}
