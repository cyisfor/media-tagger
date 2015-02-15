#include "memory.h"
#include "record.h"
#include <assert.h>

#include <stdio.h>

typedef void* pointer;

typedef struct context_s {
  size_t size;
  void* data;
} context;

struct {
  ssize_t num;
  context* stack;
} contexts = { 0, NULL };

/* the idea is blocks of memory as length-data-data-data-etc
 * ignore when data is freed, but when context is popped, all length-data things are freed
 * allows small allocations in one large block.
 * also allows parent application to do the freeing, even if module fails to call free.
 */

// make n round up to multiples of 1024
#define EVENOUT(n) ((n)/0x400+1)*0x400

void memory_pushContext(void) {
  ++contexts.num;
  contexts.stack = realloc(contexts.stack,EVENOUT(sizeof(context) * contexts.num));
  context* new = contexts.stack + contexts.num - 1;
  new->size = 0;
  new->data = NULL;
}

void memory_popContext(void) {
  if(contexts.num == 0) return;
  record(INFO,"num %d\n",contexts.num);

  context* old = contexts.stack + contexts.num - 1;
  free(old->data);
  --contexts.num;
  contexts.stack = realloc(contexts.stack,EVENOUT(sizeof(context) * contexts.num));
}

void memory_finish(void) {
  int i;
  for(i=0;i<contexts.num;++i) {
    context* old = contexts.stack + i;
    free(old->data);
  }
  free(contexts.stack);
  contexts.stack = NULL;
  contexts.num = 0;
}

void* memory_alloc(size_t size) {
  if(contexts->num == 0) {
    memory_pushContext();
  }
  context* ctx = contexts.stack + contexts.num;
  ctx->data = realloc(ctx->data,ctx->size + size);
  void* block = ctx->data + ctx->size;
  record(INFO,"alloc %p>%d %d",block,ctx->size,size);
  ctx->size += size;
  return block;
}

void memory_free(void* buf) {
    // could set a context->freed flag...
    // or NOTHING NOTHING AHAHAHAHA
}

void* memory_realloc(void* mem, size_t size) {
  ....dammit
    need to get the existing size of this memory
    embed context into it?
    this is just rewriting malloc
    pointer buf = mem - sizeof(pointer);
    pointer below = *((pointer*)buf); // just for debugging
    buf = realloc(buf,size + sizeof(pointer));
    pointer newbelow = *((pointer*)buf);
    assert(below == newbelow);
    record(INFO,"realloc %p %d",buf,size);
    // it's rainin miracles up here!
    return buf + sizeof(pointer);
}
