/*
 * dbtop_server.h
 *
 *  Created on: Aug 13, 2012
 *      Author: alexey
 */

#ifndef DBTOP_SERVER_H_
#define DBTOP_SERVER_H_

#define DBMAPHOOK_RECHECK 5
#define DBMAPHOOK_ANTIDDOS 60

void *run_server(void *data);
int connect_to_server_dbtop();
void *renew_map_on_request(void *data);

#endif /* DBTOP_SERVER_H_ */
