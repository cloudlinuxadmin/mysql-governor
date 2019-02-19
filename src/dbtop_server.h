/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#ifndef DBTOP_SERVER_H_
#define DBTOP_SERVER_H_

#define DBMAPHOOK_RECHECK 5
#define DBMAPHOOK_ANTIDDOS 60

void *run_server (void *data);
int connect_to_server_dbtop ();
void *
renew_map_on_request (void *data);

#endif /* DBTOP_SERVER_H_ */
