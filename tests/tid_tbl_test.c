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
#include <glib.h>

#include "../src/tid_table.h"

void chek_user_perf2(gpointer key, tid_table * item, gpointer user_data) {
	printf("Item %d pid %d username %s CPU %lld READ %lld WRITE %lld\n", GPOINTER_TO_INT(key),
			item->pid, item->username, item->cpu, item->read, item->write);
}

int main() {

	client_data dt1, dt2;
	init_tid_table();
	dt1.cpu = 0;
	dt1.pid = 1;
	dt1.tid = 2;
	dt1.read = 10;
	dt1.write = 10;
	strcpy(dt1.username, "test1");
	dt1.type = 0;
	add_new_tid_data(&dt1, 0);
	printf("Add 1 item\n");
	proceed_tid_data((GHFunc) chek_user_perf2, NULL);
	dt2.cpu = 0;
	dt2.pid = 3;
	dt2.tid = 4;
	dt2.read = 11;
	dt2.write = 11;
	strcpy(dt2.username, "test2");
	dt2.type = 1;
	printf("Add 2 item\n");
	add_new_tid_data(&dt2, 0);
	proceed_tid_data((GHFunc) chek_user_perf2, NULL);
	printf("Remove 1 item\n");
	remove_tid_data(2);
	proceed_tid_data((GHFunc) chek_user_perf2, NULL);
	printf("Restore 1 item\n");
	add_new_tid_data(&dt2, 0);
	proceed_tid_data((GHFunc) chek_user_perf2, NULL);
	dt2.cpu = 1000;
	printf("Rewrite 1 item\n");
	add_new_tid_data(&dt2, 0);
	proceed_tid_data((GHFunc) chek_user_perf2, NULL);
	free_tid_table();
}
