#include "record.h"

#include <uv.h>

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

#define NUM 4
#define WORKER_LIFETIME 3600 // like an hour idk

struct lackey {
	uv_process_t process;
	uv_pipe_t pipe;
	uv_timer_t restart;
	int which;
} workers[NUM];

void start_lackey(struct lackey* who);

void lackey_restarting(uv_timer_t* handle) {
	uv_lackey_t* self = (uv_lackey_t*)handle->data;
	record(INFO,"restarting worker %d",
				 self->which);
	start_lackey(self);
}


void lackey_closed(uv_handle_t* req) {
	// magic
	uv_lackey_t* self = (uv_lackey_t*)req;
	uv_timer_start(&self->restart, lackey_restarting, RESTART_DELAY,0);
}
	

void wait_then_restart_lackey(uv_process_t *req,
															int64_t exit_status,
															int term_signal) {
	uv_lackey_t* self = (uv_lackey_t*)req;
	record(INFO,"worker %d (%d) died %d",
				 req->pid,
				 self->which,
				 exit_status);
	uv_close((uv_handle_t*)req,lackey_closed);
}

const char* lackey = NULL;
const char* filedb = NULL;

void start_lackey(struct lackey* who) {
	char* args[] = {"cgexec","-g","memory:/image_manipulation",
									lackey,NULL};
	uv_pipe_init(uv_default_loop(), &who->pipe);
	uv_stdio_container_t io = {
		.flags: UV_CREATE_PIPE | UV_READABLE_PIPE,
		.data.stream: (uv_stream_t*) &who->.pipe		
	};
	uv_process_options_t opt = {
		.exit_cb: wait_then_restart_lackey,
		.file: "cgexec",
		.args: args,
		.env: NULL,
		.cwd: filedb,
		.flags: UV_PROCESS_WINDOWS_HIDE,
		.stdio_count: 1,
		.stdio: &io
	};
	assert(0==uv_spawn(uv_default_loop(),&who->.process, &opt));
}

void lackey_init(struct lackey* self) {
	uv_timer_init(uv_default_loop(), &self->restart);
	self->restart.data = self;
}

void kill_lackey(uv_timer_t* handle) {
	// randomly kill a worker, to keep them fresh
	// b/c memory leaks in ImageMagick
	static int ctr = 0;
	// note this could kill a worker in the middle of thumbnail generation
	// but this will also kill a worker stuck in the middle of thumbnail generation
	record(INFO,"killing worker %d",ctr);
	uv_process_kill(&workers[ctr],SIGTERM);
	ctr = (ctr + 1)%NUM;
	// it'll cycle through them all in a lifetime
	// visit each once a lifetime
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


int main(int argc, char** argv) {
  dolock();

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
		filedb = strdup("/home/.local/filedb");
		record(INFO, "filedb '%s'",filedb);
	}

	uv_timer_t restart_timer;
	uv_timer_init(uv_default_loop(),&restart_timer);
	uv_timer_start(&restart_timer, kill_lackey,
								 WORKER_LIFETIME, WORKER_LIFETIME);

	int i = 0;
	record(INFO,"Firing off %d workers",NUM);
	for(;i<NUM;++i) {
		workers[i].which = i;
		start_lackey(&workers[i]);
	}
	return uv_run(uv_default_loop(), UV_RUN_DEFAULT);
}
