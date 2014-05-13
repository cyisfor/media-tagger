#include <assert.h>
#include <stdlib.h> // NULL

int main(void) {
    {
        void* one = NULL;
        void** two = &one;
        void*** three = &two;
        assert(*three == two);
        assert(*two == one);
        assert(**three == one);
    }

    {
        void* one = NULL;
        void* two = (void*)&one;
        void* three = (void*)&two;

        assert(*((void**)three) == two);
        assert(*((void**)two) == one);
        assert(*((void**)*((void**)three)) == one);
    }
    return 0;
}
