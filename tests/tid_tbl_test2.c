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

#define MX 100000
int main() {

        long i=0;
	client_data dt1, dt2;
	init_tid_table();
	
        for(i=0;i<MX;i++){
            dt1.cpu = 0;
            dt1.pid = 1;
            dt1.tid = i;
            dt1.read = 10;
            dt1.write = 10;
            strcpy(dt1.username, "test1");
            dt1.type = 0;
            add_new_tid_data(&dt1, i);
        }
        
        printf("Added\n");
        sleep(30);
        for(i=0;i<MX;i++){
            remove_tid_data(i);
        }
        printf("Removed\n");
        sleep(30);
        
        for(i=0;i<MX*2;i++){
            dt1.cpu = 0;
            dt1.pid = 1;
            dt1.tid = i;
            dt1.read = 10;
            dt1.write = 10;
            strcpy(dt1.username, "test1");
            dt1.type = 0;
            add_new_tid_data(&dt1, i);
        }
        printf("Added again\n");
        sleep(30);

	free_tid_table();
}
