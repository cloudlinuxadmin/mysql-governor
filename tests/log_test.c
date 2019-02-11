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

#include "../src/data.h"
#include "../src/log.h"
#include "../src/governor_config.h"

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

	WRITE_LOG(NULL, 0, buffer, _DBGOVERNOR_BUFFER_1024, "Message for error log (%d)", DEBUG_MODE, 500);
	Stats tst;
	tst.cpu = 1000;
	tst.read = 1001;
	tst.write = 1002;
	WRITE_LOG(&tst, 1, buffer, _DBGOVERNOR_BUFFER_1024, "Message for restrict log (%d) with stat", DEBUG_MODE, 501);
	WRITE_LOG(NULL, 1, buffer, _DBGOVERNOR_BUFFER_1024, "Message for restrict log (%d) with no stat", DEBUG_MODE, 502);

	print_config(get_config());
	close_log();
	close_restrict_log();
	printf("Test completed\n");
	return 0;
}
