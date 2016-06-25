#include "record.h"
#include "watch.h"

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

char lackey[PATH_MAX] = NULL;

void start_lackey(struct lackey* who) {
	const char* args[] = {"cgexec","-g","memory:/image_manipulation",
									lackey,NULL};
	uv_pipe_init(uv_default_loop(), &who->pipe, 1);
	uv_stdio_container_t io = {
		.flags = UV_CREATE_PIPE | UV_READABLE_PIPE,
		.data.stream = (uv_stream_t*) &who->pipe		
	};
	uv_process_options_t opt = {
		.exit_cb = wait_then_restart_lackey,
		.file = "cgexec",
		.args = (char**)args,
		.env = NULL,
		.flags = UV_PROCESS_WINDOWS_HIDE,
		.stdio_count = 1,
		.stdio = &io
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
	uv_write_t req;
	uv_timer_t timer; // have to set ->data for this...
	struct message message;
	int which;
};

static void maybe_send_to_worker(struct writing* self);
static void send_to_a_worker(void* udata, const char* filename) {
	uint32_t ident = strtol(filename,NULL,0x10);
	assert(ident > 0 && ident < (1<<7)); // can bump 1<<7 up in message.h l8r
	
	int fd = open(filename,O_RDONLY);
	if(fd == -1) {
		// got deleted somehow
		return;
	}
	// regardless of success, if fail this'll just repeatedly fail 
  // so delete it anyway
  unlink(name);

	char buf[0x100];
	ssize_t len = read(fd,buf,0x100);
	
	struct writing* self = malloc(sizeof(struct writinng));
	uv_timer_init(uv_default_loop(),&self->timer);
	self->timer.data = self;
	self->which = 0;
	
	self->m.resize = false;
	self->m.id = ident;
	
	if(len) {
		buf[len] = '\0';
		uint32_t width = strtol(buf, NULL, 0x10);
		if(width > 0) {
			record(INFO,"Got width %x, sending resize request",width);
			self->m.resize = true;
			self->m.resized.width = width;
		}
	}
	
	// pick a worker who isn't busy, or wait for one to finish.
	// workers should only be busy if the write fails.
	maybe_send_to_worker(self);
}

static void maybe_written(uv_write_t* req, int status);
static void maybe_send_to_worker(struct writing* self) {
	uv_write(&self->req, (uv_stream_t*)&workers[which].pipe,
					 &self->message, sizeof(struct message), maybe_written);
}

static void retry_send_places(uv_timer_t* req);
static void maybe_written(uv_write_t* req, int status) {
	struct writing* self = (struct writing*)req;
	if(status == 0) {
		free(self);
		return;
	}
	record(INFO,"Sending message to worker %d failed",self->which);
	if(self->which == NUM) {
		self->which = 0;
		uv_timer_start(&self->timer, retry_send_places, 1000, 0);
	} else {
		++self.which;
		maybe_send_to_worker(self);
	}
}

static void retry_send_places(uv_timer_t* req) {
	struct writing* self = (struct writing*)req->data;
	record(WARNING,"Retrying sending %x to all workers...",
				 self->message.id);
	maybe_send_to_worker(self);
}

int main(int argc, char** argv) {
  dolock();

	srand(time(NULL));
	recordInit();
	ssize_t amt;
	char* lastslash = strrchr(argv[0],'/');
	if(lastslash == NULL) {
		realpath("./lackey-bin",lackey);
	} else {
		realpath(argv[0],lackey);
		// take the real path of us, and convert the end to lackey-bin
		amt = lastslash - argv[0] + 1;
		memcpy(lackey+amt,"lackey-bin",sizeof("lackey-bin"));
		lackey[amt+sizeof("lackey-bin")-1] = '\0';
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
		.f = send_to_a_worker,
		.udata = NULL
	};
	watch_dir(&watchreq,
						".",
						&handle);				
						
	return uv_run(uv_default_loop(), UV_RUN_DEFAULT);
}
