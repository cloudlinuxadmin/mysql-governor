#include <klee/klee.h>

#include <stdio.h>

#include <fifo_stats.h>

void dump_stat(Stats *st)
{
    printf("stat.cpu %g; stat.write %lld; stat.read %lld\n", st->cpu, st->write, st->read);
}

int main() {
    uint64_t fifo_ptr; // struct fifo_stats *
    uint64_t stats_ptr; // Stats *

    klee_make_symbolic(&fifo_ptr, sizeof(uint64_t), "fifo_ptr");
    klee_make_symbolic(&stats_ptr, sizeof(uint64_t), "stats_ptr");

    fifo_ptr = (uint64_t) fifo_stats_init(1000);

    Stats s1, s2, s3;

    s1.cpu = 0.34;
    s1.write = 2570000;
    s1.read = 36400000;
    stats_ptr = (uint64_t)fifo_stats_push((struct fifo_stats *) fifo_ptr, &s1);

    s2.cpu = 1.12;
    s2.write = 1;
    s2.read = 0;
    stats_ptr = (uint64_t)fifo_stats_push((struct fifo_stats *) fifo_ptr, &s2);

    s3.cpu = 456.64;
    s3.write = 2341;
    s3.read = 10;
    stats_ptr = (uint64_t)fifo_stats_push((struct fifo_stats *) fifo_ptr, &s3);

    fifo_stats_foreach((struct fifo_stats *)fifo_ptr, dump_stat);

    fifo_stats_free((struct fifo_stats *) fifo_ptr);

    return 0;
}
