#include <klee/klee.h>

#include <fifo_stats.h>

int main() {
    uint64_t ptr; // struct fifo_stats *
    klee_make_symbolic(&ptr, sizeof(uint64_t), "ptr");

    ptr = (uint64_t) fifo_stats_init(1000);

    return 0;
}
