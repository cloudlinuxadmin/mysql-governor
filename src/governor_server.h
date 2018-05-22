/*
 * governor_server.h
 *
 *  Created on: Aug 6, 2012
 *      Author: alexey
 */

#ifndef GOVERNOR_SERVER_H_
#define GOVERNOR_SERVER_H_

void create_socket();
void *get_data_from_client(void *data);
int get_soket();
void monitor_data_from_client(void *data);
void *proceed_data_every_second(void *data);

#endif /* GOVERNOR_SERVER_H_ */
