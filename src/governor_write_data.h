/*
 * governor_write_data.h
 *
 *  Created on: Aug 6, 2012
 *      Author: alexey
 */

#ifndef GOVERNOR_WRITE_DATA_H_
#define GOVERNOR_WRITE_DATA_H_

#include <stdint.h>

typedef struct _sock_data{
	int socket;
	int status;
} sock_data;

int connect_to_server();
int send_info_begin(char *username);
int send_info_end(char *username);
int close_sock();
sock_data *get_sock();

void *governor_load_lve_library();
int governor_init_lve();
void governor_destroy_lve();
int governor_enter_lve(uint32_t *cookie, char *username);
void governor_lve_exit(uint32_t *cookie);
int governor_enter_lve_light(uint32_t *cookie);
void governor_lve_exit_null();
int governor_lve_enter_pid(pid_t pid);
int governor_lve_enter_pid_user(pid_t pid, char *username);


#endif /* GOVERNOR_WRITE_DATA_H_ */
