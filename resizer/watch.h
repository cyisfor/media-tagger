struct watcher {
	void (*f)(void*, const char* filename);
	void* udata;
};

#include <uv.h>

void watch_dir(uv_fs_event_t* req,
							 const char* location,
							 struct watcher* handle);
