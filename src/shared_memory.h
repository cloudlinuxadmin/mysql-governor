/*
 * shared_memory.h
 *
 *  Created on: Sep 10, 2012
 *      Author: alexey
 */

#ifndef SHARED_MEMORY_H_
#define SHARED_MEMORY_H_

int init_bad_users_list();
void clear_bad_users_list();
int remove_bad_users_list();
int is_user_in_list(char *username);
int add_user_to_list(char *username);
int delete_user_from_list(char *username);
long get_users_list_size();
void printf_bad_users_list();

int32_t is_user_in_bad_list_cleint(char *username);
int init_bad_users_list_client();
int remove_bad_users_list_client();
int32_t is_user_in_bad_list_cleint_persistent(char *username);
int user_in_bad_list_cleint_show();
int init_bad_users_list_utility();
int remove_bad_users_list_utility();

#endif /* SHARED_MEMORY_H_ */
