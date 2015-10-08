/*
 * shared_memory.h
 *
 *  Created on: Sep 10, 2012
 *      Author: alexey
 */

#ifndef SHARED_MEMORY_H_
#define SHARED_MEMORY_H_

#ifdef HAVE_MMAP64
#define cl_mmap(a,b,c,d,e,f)    mmap64(a,b,c,d,e,f)
#else
#define cl_mmap(a,b,c,d,e,f)    mmap(a,b,c,d,e,f)
#endif
#define cl_munmap(a,b)          munmap((a),(b))

int init_bad_users_list();
void clear_bad_users_list();
int remove_bad_users_list();
int is_user_in_list(char *username);
int add_user_to_list(char *username, int is_all);
int delete_user_from_list(char *username);
long get_users_list_size();
void printf_bad_users_list();
int delete_allusers_from_list();

int32_t is_user_in_bad_list_cleint(char *username);
int init_bad_users_list_client();
int remove_bad_users_list_client();
int32_t is_user_in_bad_list_cleint_persistent(char *username);
int user_in_bad_list_cleint_show();
int init_bad_users_list_utility();
int remove_bad_users_list_utility();
int init_bad_users_list_if_not_exitst();
void printf_bad_list_cleint_persistent(void);

#endif /* SHARED_MEMORY_H_ */
