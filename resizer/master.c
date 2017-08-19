#include "record.h"
#include "watch.h"
#include "message.h"

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
}

struct diedmsg {
	int pid;
	int status;
};

int died[2];

void on_chld(int signum) {
	for(;;) {
		struct diedmsg msg;
		msg.pid = waitpid(-1,&msg.status,WNOHANG);
		if(msg.pid < 0) {
			if(errno == EINTR) continue;
			assert(errno == EAGAIN);
			break;
		}
		for(;;) {
			// shouldn't block for small messages, if we drain it soon enough.
			int res = write(died[1],&msg,sizeof(msg));
			if(res < 0) {
				if(errno == EINTR) continue;
				perror("died");
				abort();
			}
		}
	}
}

void worker_died(int pid, int status) {
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

struct writing {
	uv_timer_t timer;
	struct message message;
	int which;
};

static void send_to_a_worker(struct writing* self);
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
	signal(SIGPIPE,SIG_IGN);
	signal(SIGCHLD,SIG_IGN);
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
	pipe(died);
	int watcher = inotify_init();

	struct pollfd pfd[] = {
		{
			.fd = watcher,
			.events = POLLIN
		},
		{
			.fd = died[0],
			.events = POLLIN
		},
		{
			.fd = queue[1],
			.events = 0
		}
	};

	inotify_add_watch(watcher,".",IN_MOVED_TO);
	int timeout;
	struct message message = {};
	
	for(;;) {
		// ramp up timeout the more workers we have hanging out there
		if(pfd[2].events == 0) timeout = -1;
		else if(numworkers == 1) timeout = 100;
		else if(numworkers == 2) timeout = 500;
		else if(numworkers == 3) timeout = 3000;
		else timeout = WORKER_LIFETIME;

		int res = poll((struct pollfd*)&pfd,pfd[2].events ? 3 : 2,timeout);
		if(res < 0) {
			if(errno == EINTR) continue;
			perror("poll");
			abort();
		}
		if(res == 0) {
			assert(pfd[2].events);
			if(numworkers >= NUM) {
				stop_a_worker();
			}
			start_worker();
			poll(NULL,0,100); // wait a bit
			continue;
		}
		if(pfd[0].revents) {
			// file changed
			struct inotify_event ev;
			ssize_t amt = read(watcher,&ev,sizeof(ev));
			if(amt < 0) {
				perror("file changed");
				assert(errno == EINTR || errno == EAGAIN);
			} else {
				assert(sizeof(ev) == amt);
				if(file_changed(&message, ev.name)) {
					if(numworkers == 0)
						start_worker(); // start at least one

					pfd[2].events = POLLOUT;
				}
			}
		} else if(pfd[2].revents) {			
			// queue ready for writing
			ssize_t res = write(queue[1],&message,sizeof(message));
			assert(res == sizeof(message));
			pfd[1].events = 0;
		} else if(pfd[1].revents) {
			// something died
			struct diedmsg msg;
			ssize_t amt = read(died[0],&msg,sizeof(msg));
			assert(amt == sizeof(msg));
			worker_died(msg.pid, msg.status);
		} 
			
	}
			
}
