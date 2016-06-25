struct linebuf {
	uv_buf_t buf;
	size_t space;
	char delim;
	void* end;
	void* beginning;
};

bool linebuf_read(struct linebuf* self, int fd) {
	for(;;) {
		if(self->space < 0x100) {
			self->space = 0x1000;
			self->buf.base = realloc(self->buf.base,
															 self->buf.len+self->space);
		}
		ssize_t amt = recv(fd, self->buf.base, self->space, MSG_DONTWAIT);
		if(amt == 0) {
			record(ERROR,"Connection closed.");
			// probably shouldn't try to get partial line here, eh
			self->end = self->buf.base + self->buf.len;
			return true;
		}
		if(amt < 0) {
			if(errno == EAGAIN) {
				// done feeding, yay
				self->done = true;
				return false;
			}
			record(ERROR,"Bad error %d",errno);
			self->done = true;
			return false;
		}
		self->space -= amt;
		self->end = memchr(self->buf,self->delim,amt);
		if(self->end == NULL) {
			self->buf.len += amt;
			continue;
		}
		// found newlines, should pause to parse them out
		return true;
	}
}

bool linebuf_next(struct linebuf* self, uv_buf_t* dest) {
	if(self->end!=NULL) {
		// save partial line at the end, but memcpy to save memory
		if(self->beginning!=self->buf.base) {
			// believe it or not, memmove doesn't do this optimization
			ssize_t completed = self->beginning - self->buf.base;
			ssize_t left = self->buf.len - completed;
			if(left < completed) {
				// non-overlapping, just memcpy
				memcpy(self->buf.base, self->beginning, left);
			} else {
				memmove(self->buf.base, self->beginning, left);
			}
			// expand space to the stuff we just copied to safety
			self->space += self->buf.len - left;
			self->buf.len = left;
		}
		// need moar
		return false;
	} else {
		dest->base = self->beginning;
		dest->len = self->end - self->beginning;
		ssize_t completed = self->end - self->buf.base + 1;
		ssize_t left = self->buf.len - completed;
		self->beginning = self->end;
		self->end = memchr(self->end,self->delim,left);
		// but still return true, b/c we found a dest
		// even if no more lines (self->end == NULL)
		return true;
	}
}
