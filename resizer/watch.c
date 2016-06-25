#include "watch.h"

#include <uv.h>

#include <sys/types.h> // opendir etc
#include <dirent.h>
#include <assert.h>

void check(uv_fs_event_t* req, const char* filename, int events, int status) {
	assert(status >= 0);
	if(events && UV_CHANGE) {
		struct watcher* handle = (struct watcher*) req->data;
		handle->f(handle->udata, filename);
	}
}

void watch_dir(uv_fs_event_t* req,
							 const char* location,
							 struct watcher* handle) {
	// maybe race condition, so do this first.
	uv_fs_event_init(uv_default_loop(), req);
	req->data = handle;
	uv_fs_event_start(req, check, location, 0);
	
	// catchup could use the fd in the uv_fs_event_t
	// IF THEY WEREN'T ASSES ABOUT INTERFACES
	DIR* d = opendir(location);
  for(;;) {
    struct dirent* ent = readdir(d);
    if(!ent) break;
    handle->f(ent->d_name, handle->udata);
  }
  closedir(d);
}
