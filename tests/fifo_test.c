/*
 * fifo_test.c
 *
 *  Created on: Aug 13, 2012
 *      Author: alexey
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>

#include "../src/data.h"
#include "../src/fifo_stats.h"

void print_stats_m(Stats *st) {
	printf("CPU %f READ %ld WRITE %ld\n", st->cpu, st->read, st->write);
}

int main() {

	struct fifo_stats *tt = fifo_stats_init(10);

	Stats *st = malloc(sizeof(Stats));
	st->cpu = 0.1;
	st->read = 1;
	st->write = 1;

	fifo_stats_push(tt, st);

	fifo_stats_foreach(tt, print_stats_m);
	printf("-------------------\n");

	st = malloc(sizeof(Stats));
	st->cpu = 0.2;
	st->read = 2;
	st->write = 2;

	fifo_stats_push(tt, st);

	fifo_stats_foreach(tt, print_stats_m);
	printf("-------------------\n");

	st = malloc(sizeof(Stats));
	st->cpu = 0.3;
	st->read = 3;
	st->write = 3;
	fifo_stats_refresh_last(tt, st);

	fifo_stats_foreach(tt, print_stats_m);
	printf("-------------------\n");

	int i = 0;

	for (i = 1; i < 11; i++) {
		st = malloc(sizeof(Stats));
		st->cpu = 1.1 * i;
		st->read = 11 * i;
		st->write = 12 * i;

		fifo_stats_push(tt, st);

		fifo_stats_foreach(tt, print_stats_m);
		printf("-------------------\n");
	}

	fifo_stats_free(tt);

	return 0;
}
