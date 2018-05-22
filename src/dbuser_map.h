/* Copyright Cloud Linux Inc 2010-2013 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbuser_map.h
 *
 *  Created on: Jul 2, 2013
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
 */


#ifndef __DBUSER_MAP__
#define __DBUSER_MAP__

#include <sys/types.h>
#include <sys/stat.h>
#include <time.h>
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>

#include "data.h"

#define RLOCK F_RDLCK
#define WLOCK F_WRLCK

time_t last_modify_map();
int get_map_file();
int get_uid(username_t u);
char *get_account(username_t u);

int lock_read_map();
int lock_write_map();
int unlock_rdwr_map();

void *parse_map_file_every_hour(void *data);
void trim(char *s);

#endif /* __DBUSER_MAP__ */
