#include "memory.h"
#include "record.h"
#include <assert.h>

#include <stdio.h>

struct context_s {
  struct context_s* lower;
} *contexts = NULL;

/* just use talloc to track this shit
 */

void memory_pushContext(void) {
  struct context_s* new = talloc(contexts,struct context_s);
  new->lower = contexts;
  contexts = new;
}

void memory_popContext(void) {
  if(contexts == NULL) {
    record(ERROR, "no contexts?");
    return;
  }
  struct context_s* lower = contexts->next;
  talloc_free(contexts);
  contexts = lower;
}

void memory_finish(void) {    
    while(contexts != NULL) {
        memory_popContext();
    }
}

void* memory_alloc(size_t size) {
  return talloc_size(contexts,size);
}

void memory_free(void* buf) {
    // could set a context->freed flag...
    // or NOTHING NOTHING AHAHAHAHA
}

void* memory_realloc(void* mem, size_t size) {
  return talloc_realloc_size(contexts, mem, size);
}
