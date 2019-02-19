/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>

#include "../src/governor_server.h"
#include "../src/log.h"
#include "../src/governor_config.h"
#include "../src/tid_table.h"
#include "../src/parce_proc_fs.h"
#include "../src/calc_stats.h"
#include "../src/tick_generator.h"
#include "../src/commands.h"

int main(){

	config_init("../db-governor.xml.test");

	if (open_log ("test1.log")){
		printf("Can't open log file %d\n", errno);
		return -1;
	}
	if(open_restrict_log ("test2.log")){
		printf("Can't open restrict log file %d\n", errno);
		close_log();
		return -1;
	}

	printf("Log1 %p log2 %p\n", get_log(), get_restrict_log());

	char buffer[_DBGOVERNOR_BUFFER_1024];

	print_config(get_config());

	init_accounts_and_users();
	print_to_restrict_log_stats(NULL);
	client_data message;
	tid_table *tbl = malloc(sizeof(tid_table));
	memset(&message, (int)0, sizeof(message));
	memset(tbl, (int)0, sizeof(tid_table));
	strcpy(message.username, "test1");
	strcpy(tbl->username, "test1");
	Stats *st = malloc(sizeof(Stats));
	clac_stats_difference(&message, tbl, st);
	add_new_stats(tbl->username, st, get_current_tick());
	print_to_restrict_log_stats(NULL);
	free_accounts_and_users();

	close_log();
	close_restrict_log();
	printf("Test completed\n");
	return 0;
}
