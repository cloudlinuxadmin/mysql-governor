/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <errno.h>

#include "../src/data.h"
#include "../src/log.h"
#include "../src/governor_config.h"
#include "../src/governor_write_data.h"
#include "../src/governor_server.h"
#include "../src/tid_table.h"
#include "../src/parce_proc_fs.h"

int try = 0;

void *task(void *arg) {
	int ret;
	ret = send_info_begin("test1");
#ifdef TEST
		printf("Send begin info %d, %d - return %d\n", sd->socket, sd->status, ret);
#endif
	long rr = rand() % 20 + 1;
	printf("Try %d will executing %ld\n", try, rr);
	long diff = 0;
	time_t t1 = time(NULL);
	while (diff < rr) {
		long iii = rr * 10000;
		while (iii)
			iii--;
		diff = time(NULL) - t1;
	}
	printf("Try %d will executing %ld done\n", try, rr);
	ret = send_info_end("test1");
#ifdef TEST
		printf("Send begin info %d, %d- return %d\n",sd->socket, sd->status, ret);
#endif
	return NULL;
}

int main() {
	printf("Main daemon started\n");
	pid_t pid = 0;
	int chld_state;

	config_init("../db-governor.xml.test");

	if (open_log("test1.log")) {
		printf("Can't open log file %d\n", errno);
	}
	if (open_restrict_log("test2.log")) {
		printf("Can't open restrict log file %d\n", errno);
		close_log();
	}
	print_config(get_config());

	pid = fork();
	if (pid < 0) {
		return -1;
	}
	if (pid > 0) {

		init_tid_table();
		dbgov_init();
		//Work cycle
		create_socket();

		get_data_from_client(NULL);

		waitpid(pid, &chld_state, 0);
		printf("Main daemon restart child\n");
	}
	if (pid == 0) {
		close_log();
		close_restrict_log();
		connect_to_server();
		sleep(5);
		while (try < 3) {
			try++;
			int rr = rand() % 2 + 1;
			pthread_t t1[rr];
			int i = 0;
			printf("Try %d Will start %d\n", try, rr);
			for (i = 0; i < rr; i++) {
				if (pthread_create(&t1[i], NULL, task, NULL) != 0) {
					printf("Try %d - %d pthread_create() error\n", try, i);
				} else {
					printf("Try %d - %d pthread_create()\n", try, i);
				}
			}
			for (i = 0; i < rr; i++) {
				pthread_join(t1[i], NULL);
			}
		}
		close_sock();
		return 0;
	}

	close_log();
	close_restrict_log();
	printf("Main daemon terminated\n");
}
