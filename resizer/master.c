#include "record.h"
#include "watch.h"
#include "message.h"

#include <uv.h>

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

struct lackey {
	uv_process_t process;
	uv_pipe_t pipe;
	uv_timer_t restart;
	int which;
} workers[NUM];

void start_lackey(struct lackey* who);

void lackey_restarting(uv_timer_t* handle) {
	struct lackey* self = (struct lackey*)handle->data;
	record(INFO,"restarting worker %d",
				 self->which);
	start_lackey(self);
}


void lackey_closed(uv_handle_t* req) {
	// magic
	struct lackey* self = (struct lackey*)req;
	uv_timer_start(&self->restart, lackey_restarting, RESTART_DELAY,0);
}
	

void wait_then_restart_lackey(uv_process_t *req,
															int64_t exit_status,
															int term_signal) {
	struct lackey* self = (struct lackey*)req;
	record(INFO,"worker %d (%d) died %d",
				 req->pid,
				 self->which,
				 exit_status);
	uv_close((uv_handle_t*)req,lackey_closed);
}

char lackey[PATH_MAX];

void start_lackey(struct lackey* who) {
	const char* args[] = {"cgexec","-g","memory:/image_manipulation",
									lackey,NULL};
	uv_pipe_init(uv_default_loop(), &who->pipe, 1);
	uv_stdio_container_t io[3] = {
		{
			.flags = UV_CREATE_PIPE | UV_READABLE_PIPE,
			.data.stream = (uv_stream_t*) &who->pipe		
		},
		{
			// stdout
			.flags = UV_INHERIT_FD
		},
		{
			// stderr
			.flags = UV_INHERIT_FD
		}
	};

	uv_process_options_t opt = {
		.exit_cb = wait_then_restart_lackey,
		.file = "cgexec",
		.args = (char**)args,
		.cwd = "..",
		.env = NULL,
		.flags = UV_PROCESS_WINDOWS_HIDE,
		.stdio_count = 3,
		.stdio = io
	};
	assert(0==uv_spawn(uv_default_loop(),&who->process, &opt));
}

void lackey_init(struct lackey* self, int which) {
	uv_timer_init(uv_default_loop(), &self->restart);
	self->restart.data = self;
	self->which = which; // derp
	start_lackey(self);
}

void kill_lackey(uv_timer_t* handle) {
	// randomly kill a worker, to keep them fresh
	// b/c memory leaks in ImageMagick
	static int ctr = 0;
	// note this could kill a worker in the middle of thumbnail generation
	// but this will also kill a worker stuck in the middle of thumbnail generation
	record(INFO,"killing worker %d",ctr);
	uv_process_kill(&workers[ctr].process,SIGTERM);
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

struct writing {
	uv_timer_t timer;
	struct message message;
	int which;
};

static void send_to_a_worker(struct writing* self);
static void file_changed(void* udata, const char* filename) {
	if(filename[0] == '\0' || filename[0] == '.') return;
	
	uint32_t ident = strtol(filename,NULL,0x10);
	assert(ident > 0 && ident < (1<<31)); // can bump 1<<31 up in message.h l8r
	
	int fd = open(filename,O_RDONLY);
	if(fd == -1) {
		// got deleted somehow
		return;
	}
	// regardless of success, if fail this'll just repeatedly fail 
  // so delete it anyway
  unlink(filename);

	char buf[0x100];
	ssize_t len = read(fd,buf,0x100);
	
	struct writing* self = malloc(sizeof(struct writing));
	uv_timer_init(uv_default_loop(),&self->timer);
	self->which = 0;
	
	self->message.resize = false;
	self->message.id = ident;
	
	if(len) {
		buf[len] = '\0';
		uint32_t width = strtol(buf, NULL, 0x10);
		if(width > 0) {
			record(INFO,"Got width %x, sending resize request",width);
			self->message.resize = true;
			self->message.resized.width = width;
		}
	}
	
	// pick a worker who isn't busy, or wait for one to finish.
	// workers should only be busy if the write fails.
	send_to_a_worker(self);
}

static void retry_send_places(uv_timer_t* req);
static void send_to_a_worker(struct writing* self) {
	uv_buf_t buf = {
		.base = (void*)&self->message,
		.len = sizeof(self->message)
	};
	int i;
	// cycle around the workers naturally this way.
	static int start = 0;
	++start;
	for(i=0;i<NUM;++i) {
		int which = (start + i) % NUM;
		int err =
			uv_try_write((uv_stream_t*)&workers[which].pipe, &buf, 1);
		if(err >= 0) {
			free(self);
			return;
		}
		if(err == EAGAIN) {
			record(INFO,"Sending message to worker %d failed",which);
		} else {
			record(ERROR,"Write error on worker %d!",which);
		}
	}
	record(WARNING,"No workers could take our message!");
	uv_timer_start(&self->timer, retry_send_places, 1000, 0);
}

static void retry_send_places(uv_timer_t* req) {
	// magic
	struct writing* self = (struct writing*)req;
	record(WARNING,"Retrying sending %x to all workers...",
				 self->message.id);
	send_to_a_worker(self);
}

int main(int argc, char** argv) {
	record(ERROR,"error");
  record(WARN,"warning");
  record(INFO,"info");
  record(DEBUG,"debug");
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

	uv_timer_t restart_timer;
	uv_timer_init(uv_default_loop(),&restart_timer);
	uv_timer_start(&restart_timer, kill_lackey,
								 WORKER_LIFETIME, WORKER_LIFETIME);

	int i = 0;
	record(INFO,"Firing off %d workers",NUM);
	for(;i<NUM;++i) {
		lackey_init(&workers[i], i);
	}

	uv_fs_event_t watchreq;
	struct watcher handle = {
		.f = file_changed,
		.udata = NULL
	};
	watch_dir(&watchreq,
						".",
						&handle);				
						
	return uv_run(uv_default_loop(), UV_RUN_DEFAULT);
}
