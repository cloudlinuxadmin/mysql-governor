/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <errno.h>

#include <linux/unistd.h>
#include <stdint.h>

#define my_pthread_fastmutex_t pthread_mutex_t
#define my_pthread_fastmutex_lock pthread_mutex_lock

int governor_enter_lve(uint32_t *u0, char *u1){
	printf("User %s - %d, governor_enter_lve\n", u1, *u0);
	return 0;
}

void governor_lve_exit(uint32_t *u1){
	printf("%d, governor_lve_exit\n", *u1);
}

int governor_enter_lve_light(uint32_t *u1){
	printf("%d, governor_enter_lve_light\n", *u1);
	return 0;
}

void governor_lve_exit_null(){
	printf("governor_lve_exit_null\n");
}

int governor_lve_enter_pid(pid_t u1){
	printf("%d, governor_lve_enter_pid\n", u1);
}

__thread uint32_t lve_cookie = 0;

pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;

typedef struct __mysql_mutex {
       pid_t *key;
       int is_in_lve;
       int is_in_mutex;
       int put_in_lve;
       int is_no_eneter;
} mysql_mutex;

__thread mysql_mutex *mysql_lve_mutex_governor_ptr = 0;

pthread_mutex_t mtx_mysql_lve_mutex_governor_ptr = PTHREAD_MUTEX_INITIALIZER;

__attribute__((noinline)) void unlock_mutex_lve() {
	if (mysql_lve_mutex_governor_ptr) {
	    if (mysql_lve_mutex_governor_ptr->is_in_lve == 1) {
	       governor_lve_exit(&lve_cookie);
	    }
	    mysql_lve_mutex_governor_ptr->is_no_eneter = 1;
	}
	printf("unlock_mutex_lve is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
}

__attribute__((noinline)) void lock_mutex_lve() {
     if (mysql_lve_mutex_governor_ptr) {
            if ((mysql_lve_mutex_governor_ptr->is_in_lve == 2)
                            && governor_enter_lve_light) {
					if (!governor_enter_lve_light(&lve_cookie)) {
		                mysql_lve_mutex_governor_ptr->is_in_lve = 1;
		            } else {
		    		    mysql_lve_mutex_governor_ptr->is_in_lve = 0;
		            }
            }
            mysql_lve_mutex_governor_ptr->is_no_eneter = 0;
    }
     printf("lock_mutex_lve is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
}

__attribute__((noinline)) void lve_thr_exit() {
       if (mysql_lve_mutex_governor_ptr && mysql_lve_mutex_governor_ptr->is_in_lve
                      == 1) {
               governor_lve_exit(&lve_cookie);
               mysql_lve_mutex_governor_ptr->is_in_lve = 0;
       }
       printf("lve_thr_exit is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
}

__attribute__((noinline)) int put_in_lve(char *user) {
       if (mysql_lve_mutex_governor_ptr) {
               if (!governor_enter_lve(&lve_cookie, user)) {
                       mysql_lve_mutex_governor_ptr->is_in_lve = 1;
               }
               mysql_lve_mutex_governor_ptr->is_in_mutex = 0;
       }
       printf("put_in_lve is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
       return 0;
}

__attribute__((noinline)) int my_pthread_lvemutex_lock(my_pthread_fastmutex_t *mp) {
       if (mysql_lve_mutex_governor_ptr) {
               if (mysql_lve_mutex_governor_ptr->is_in_lve == 1) {
                       governor_lve_exit(&lve_cookie);
                       mysql_lve_mutex_governor_ptr->is_in_lve = 2;
               } else if (mysql_lve_mutex_governor_ptr->is_in_lve > 1) {
                       mysql_lve_mutex_governor_ptr->is_in_lve++;
               } /*else if (mysql_lve_mutex_governor_ptr->put_in_lve
                               && !mysql_lve_mutex_governor_ptr->is_in_mutex) {
                       //governor_lve_exit_null();
                       mysql_lve_mutex_governor_ptr->put_in_lve = 0;
                       mysql_lve_mutex_governor_ptr->is_in_lve = 2;
               }*/
               mysql_lve_mutex_governor_ptr->is_in_mutex++;
       }
       printf("my_pthread_lvemutex_lock is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
       return my_pthread_fastmutex_lock(mp);
}

__attribute__((noinline)) int my_pthread_lvemutex_trylock(pthread_mutex_t *mutex) {
       if (mysql_lve_mutex_governor_ptr) {
               if (mysql_lve_mutex_governor_ptr->is_in_lve == 1) {
                       governor_lve_exit(&lve_cookie);
               }
       }
       int ret = pthread_mutex_trylock(mutex);
       if (mysql_lve_mutex_governor_ptr) {
           if (ret != EBUSY){
                if (mysql_lve_mutex_governor_ptr->is_in_lve == 1) {
                       mysql_lve_mutex_governor_ptr->is_in_lve = 2;
                } else if (mysql_lve_mutex_governor_ptr->is_in_lve > 1) {
                       mysql_lve_mutex_governor_ptr->is_in_lve++;
                }
                mysql_lve_mutex_governor_ptr->is_in_mutex++;
               } else {
                if (mysql_lve_mutex_governor_ptr->is_in_lve == 1){
                    if (!governor_enter_lve_light(&lve_cookie)) {
                           mysql_lve_mutex_governor_ptr->is_in_lve = 1;
                    } else {
    			   mysql_lve_mutex_governor_ptr->is_in_lve = 0;
                    }
                }
               }
       }
       printf("my_pthread_lvemutex_trylock is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
       return ret;
}


__attribute__((noinline)) int my_pthread_lvemutex_unlock(
               pthread_mutex_t *mutex) {
       int ret = pthread_mutex_unlock(mutex);
       if (mysql_lve_mutex_governor_ptr) {
               if ((mysql_lve_mutex_governor_ptr->is_in_lve == 2)
                               && governor_enter_lve_light) {
                       if (!governor_enter_lve_light(&lve_cookie)) {
                               mysql_lve_mutex_governor_ptr->is_in_lve = 1;
                       }
               } else if (mysql_lve_mutex_governor_ptr->is_in_lve > 2) {
                       mysql_lve_mutex_governor_ptr->is_in_lve--;
               }
               mysql_lve_mutex_governor_ptr->is_in_mutex--;
               /*if (mysql_lve_mutex_governor_ptr->put_in_lve
                               && !mysql_lve_mutex_governor_ptr->is_in_mutex) {
                       if (governor_enter_lve_light && !governor_enter_lve_light(
                                       &lve_cookie)) {
                               mysql_lve_mutex_governor_ptr->is_in_lve = 1;
                               mysql_lve_mutex_governor_ptr->put_in_lve = 0;
                       }
               }*/
       }
       printf("my_pthread_lvemutex_unlock is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
       return ret;
}

__attribute__((noinline)) void my_reserve_slot() {
       if (mysql_lve_mutex_governor_ptr) {
               if (mysql_lve_mutex_governor_ptr->is_in_lve == 1) {
                       governor_lve_exit(&lve_cookie);
                       mysql_lve_mutex_governor_ptr->is_in_lve = 2;
               } else if (mysql_lve_mutex_governor_ptr->is_in_lve > 1) {
                       mysql_lve_mutex_governor_ptr->is_in_lve++;
               } /*else if (mysql_lve_mutex_governor_ptr->put_in_lve
                               && !mysql_lve_mutex_governor_ptr->is_in_mutex) {
                       //governor_lve_exit_null();
                       mysql_lve_mutex_governor_ptr->put_in_lve = 0;
                       mysql_lve_mutex_governor_ptr->is_in_lve = 2;
               }*/
               mysql_lve_mutex_governor_ptr->is_in_mutex++;
       }
       printf("my_reserve_slot is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
       return;
}

__attribute__((noinline)) void my_release_slot() {
       if (mysql_lve_mutex_governor_ptr) {
               if ((mysql_lve_mutex_governor_ptr->is_in_lve == 2)
                               && governor_enter_lve_light) {
                       if (!governor_enter_lve_light(&lve_cookie)) {
                               mysql_lve_mutex_governor_ptr->is_in_lve = 1;
                       }
               } else if (mysql_lve_mutex_governor_ptr->is_in_lve > 2) {
                       mysql_lve_mutex_governor_ptr->is_in_lve--;
               }
               mysql_lve_mutex_governor_ptr->is_in_mutex--;
               /*if (mysql_lve_mutex_governor_ptr->put_in_lve
                               && !mysql_lve_mutex_governor_ptr->is_in_mutex) {
                       if (governor_enter_lve_light && !governor_enter_lve_light(
                                       &lve_cookie)) {
                               mysql_lve_mutex_governor_ptr->is_in_lve = 1;
                               mysql_lve_mutex_governor_ptr->put_in_lve = 0;
                       }
               }*/
       }
       printf("my_release_slot is_in_lve %d is_in_mutex %d is_no_eneter %d put_in_lve %d\n", mysql_lve_mutex_governor_ptr->is_in_lve, mysql_lve_mutex_governor_ptr->is_in_mutex, mysql_lve_mutex_governor_ptr->is_no_eneter, mysql_lve_mutex_governor_ptr->put_in_lve);
       return;
}

int cahce(){
	pthread_mutex_t mt = PTHREAD_MUTEX_INITIALIZER;
	pthread_mutex_t mt2 = PTHREAD_MUTEX_INITIALIZER;
	my_reserve_slot();

	my_pthread_lvemutex_lock(&mt);
	my_pthread_lvemutex_lock(&mt2);

	my_pthread_lvemutex_unlock(&mt2);
	my_pthread_lvemutex_unlock(&mt);
	my_release_slot();

}

int main(){

	pthread_mutex_t mt = PTHREAD_MUTEX_INITIALIZER;
	pthread_mutex_t mt1 = PTHREAD_MUTEX_INITIALIZER;
	pthread_mutex_t mt2 = PTHREAD_MUTEX_INITIALIZER;
	mysql_lve_mutex_governor_ptr = malloc(sizeof(mysql_mutex));

	put_in_lve("user1");

	my_pthread_lvemutex_lock(&mt);
	my_pthread_lvemutex_lock(&mt1);
	my_pthread_lvemutex_lock(&mt2);

	my_reserve_slot();
	cahce();
	my_release_slot();

	my_pthread_lvemutex_unlock(&mt2);
	my_pthread_lvemutex_unlock(&mt1);
	cahce();
	my_pthread_lvemutex_unlock(&mt);

	cahce();

	my_reserve_slot();
	my_pthread_lvemutex_lock(&mt1);
	my_pthread_lvemutex_unlock(&mt1);
	my_release_slot();

	my_pthread_lvemutex_lock(&mt1);
	my_pthread_lvemutex_unlock(&mt1);

	lve_thr_exit();

	free(mysql_lve_mutex_governor_ptr);
	return 0;
}
