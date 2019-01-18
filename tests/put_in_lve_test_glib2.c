/*
 * put_in_lve_test.c
 *
 *  Created on: Dec 11, 2012
 *      Author: alexey
 */

/*
 * emulator.c
 *
 *  Created on: Jul 31, 2012
 *      Author: alexey
 */

#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <errno.h>

#include "mysys_priv.h"
#include <keycache.h>
#include <hash.h>
#include <m_string.h>

#include "../src/data.h"
#include "../src/log.h"
#include "../src/governor_config.h"
#include "../src/governor_write_data.h"
#include "../src/governor_server.h"
#include "../src/tid_table.h"
#include "../src/parce_proc_fs.h"

extern CHARSET_INFO my_charset_latin1_bin;
CHARSET_INFO governor_charset_bin;

#ifdef DBG
#define TRYS_NMB 1
#else
#define TRYS_NMB 300000
#endif

int try = 0;

__thread uint32_t lve_cookie = 0;

pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;

typedef struct __mysql_mutex {
	pid_t key;
	int is_in_lve;
	int is_in_mutex;
	int put_in_lve;
} mysql_mutex;

static HASH *mysql_lve_mutex_governor = NULL;

__thread mysql_mutex *mysql_lve_mutex_governor_ptr = 0;

pthread_mutex_t mtx_mysql_lve_mutex_governor_ptr = PTHREAD_MUTEX_INITIALIZER;

void governor_value_destroyed(mysql_mutex *data) {
	free(data);
}

uchar *governor_get_key_table_mutex(mysql_mutex *table_mutex, size_t *length,
		my_bool not_used __attribute__((unused))) {
	*length = sizeof(table_mutex->key);
	return (uchar*) table_mutex->key;
}

#if !defined(max)
#define max(a, b)	((a) > (b) ? (a) : (b))
#define min(a, b)	((a) < (b) ? (a) : (b))
#endif

/*
 *   RETURN
 * < 0	s < t
 * 0	s == t
 * > 0	s > t
 */
static int governor_my_strnncoll_8bit_bin(CHARSET_INFO * cs __attribute__((unused)), const uchar *s,
		size_t slen, const uchar *t, size_t tlen, my_bool t_is_prefix) {
	int res = 0;
	if (s < t)
		res = -1;
	else if (s == t)
		res = 0;
	else
		res = 1;
	return res;
}

void governor_hash_sort_8bit_bin(CHARSET_INFO *cs __attribute__((unused)),
                           const uchar *key, size_t len,
                           ulong *nr1, ulong *nr2)
{
  return;
}

HASH *governor_create_hash_table() {
	mysql_lve_mutex_governor = (HASH *) calloc(1, sizeof(HASH));
	if (mysql_lve_mutex_governor) {
		memcpy(&governor_charset_bin, &my_charset_latin1_bin,
				sizeof(CHARSET_INFO));
		governor_charset_bin.coll->strnncoll = governor_my_strnncoll_8bit_bin;
		governor_charset_bin.coll->hash_sort = governor_hash_sort_8bit_bin;
		if (hash_init(mysql_lve_mutex_governor, &governor_charset_bin, 500, 0,
				0, (hash_get_key) governor_get_key_table_mutex,
				(hash_free_key) governor_value_destroyed, 0)) {
			mysql_lve_mutex_governor = NULL;
		}
	}
	return mysql_lve_mutex_governor;
}

int governor_add_mysql_thread_info() {
	pthread_mutex_lock(&mtx_mysql_lve_mutex_governor_ptr);
	mysql_mutex *mm = NULL;
	if (!mysql_lve_mutex_governor) {
		mysql_lve_mutex_governor = governor_create_hash_table();
		if (!mysql_lve_mutex_governor)
			return -1;
	}
	mm = (mysql_mutex *) hash_search(mysql_lve_mutex_governor,
			(uchar *) gettid(), sizeof(pid_t));
	if (!mm) {
		mm = (mysql_mutex *) calloc(1, sizeof(mysql_mutex));
		if (!mm)
			return -1;
		mm->key = gettid();
		if (hash_insert(mysql_lve_mutex_governor, (uchar *) mm)) {
			free(mm);
			return -1;
		}
	}
	pthread_mutex_unlock(&mtx_mysql_lve_mutex_governor_ptr);
	mysql_lve_mutex_governor_ptr = mm;
	return 0;
}

void governor_remove_mysql_thread_info() {
	pthread_mutex_lock(&mtx_mysql_lve_mutex_governor_ptr);
	mysql_mutex *mm = NULL;
	if (mysql_lve_mutex_governor) {
		mm = (mysql_mutex *) hash_search(mysql_lve_mutex_governor,
				(uchar *) gettid(), sizeof(pid_t));
		if (mm)
			hash_delete(mysql_lve_mutex_governor, (uchar *) mm);
	}
	pthread_mutex_unlock(&mtx_mysql_lve_mutex_governor_ptr);
	mysql_lve_mutex_governor_ptr = NULL;
}

void governor_setlve_mysql_thread_info(pid_t thread_id) {
	pthread_mutex_lock(&mtx_mysql_lve_mutex_governor_ptr);
	mysql_mutex *mm = NULL;
	if (mysql_lve_mutex_governor) {
		mm = (mysql_mutex *) hash_search(mysql_lve_mutex_governor,
				(uchar *) thread_id, sizeof(pid_t));
		if (mm) {
			if (!mm->is_in_lve) {
				mm->put_in_lve = 1;
				//if (mm->is_in_mutex) {
				//	mm->put_in_lve = 1;
				//} else {
				//	mm->put_in_lve = 1;
				//	governor_lve_enter_pid(thread_id);
				//}
			}
		}
	}
	pthread_mutex_unlock(&mtx_mysql_lve_mutex_governor_ptr);
}

__attribute__((noinline)) void put_in_lve(char *user) {
	governor_add_mysql_thread_info();
	if (mysql_lve_mutex_governor_ptr) {
		if (!governor_enter_lve(&lve_cookie, user)) {
			mysql_lve_mutex_governor_ptr->is_in_lve = 1;
		}
		mysql_lve_mutex_governor_ptr->is_in_mutex = 0;
	}
}

__attribute__((noinline)) void lve_thr_exit() {
	if (mysql_lve_mutex_governor_ptr && mysql_lve_mutex_governor_ptr->is_in_lve
			> 0) {
		governor_lve_exit(&lve_cookie);
		mysql_lve_mutex_governor_ptr->is_in_lve = 0;
	}
	governor_remove_mysql_thread_info();
}

__attribute__((noinline)) int my_pthread_lvemutex_lock(pthread_mutex_t *mp) {
	if (mysql_lve_mutex_governor_ptr) {
		if (mysql_lve_mutex_governor_ptr->is_in_lve == 1) {
			governor_lve_exit(&lve_cookie);
			mysql_lve_mutex_governor_ptr->is_in_lve = 2;
		} else if (mysql_lve_mutex_governor_ptr->is_in_lve > 1) {
			mysql_lve_mutex_governor_ptr->is_in_lve++;
		} else if (mysql_lve_mutex_governor_ptr->put_in_lve
				&& !mysql_lve_mutex_governor_ptr->is_in_mutex) {
			//governor_lve_exit_null();
			mysql_lve_mutex_governor_ptr->put_in_lve = 0;
			mysql_lve_mutex_governor_ptr->is_in_lve = 2;
		}
		mysql_lve_mutex_governor_ptr->is_in_mutex++;
	}
	return pthread_mutex_lock(mp);
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
		if (mysql_lve_mutex_governor_ptr->put_in_lve
				&& !mysql_lve_mutex_governor_ptr->is_in_mutex) {
			if (governor_enter_lve_light && !governor_enter_lve_light(
					&lve_cookie)) {
				mysql_lve_mutex_governor_ptr->is_in_lve = 1;
				mysql_lve_mutex_governor_ptr->put_in_lve = 0;
			}
		}
	}
	return ret;
}

void governor_detroy_mysql_thread_info() {
	if (mysql_lve_mutex_governor) {
		pthread_mutex_lock(&mtx_mysql_lve_mutex_governor_ptr);
		hash_free(mysql_lve_mutex_governor);
		pthread_mutex_unlock(&mtx_mysql_lve_mutex_governor_ptr);
	}
}

void load_lbr() {
	governor_load_lve_library();
}

void print_avail_thrs() {
	printf("--------------------------------------------------------\n");
	if (mysql_lve_mutex_governor) {
		HASH_SEARCH_STATE state;
		mysql_mutex *item;
		pid_t key;
		for (item = (mysql_mutex *) hash_first(mysql_lve_mutex_governor,
				(uchar*) &key, sizeof(pid_t), &state); item; item
				= (mysql_mutex *) hash_next(mysql_lve_mutex_governor,
						(uchar*) &key, sizeof(pid_t), &state)) {
			printf(
					"Item %d --- is_in_lve %d --- is_in_mutex %d -- put_in_lve %d\n",
					key, item->is_in_lve, item->is_in_mutex, item->put_in_lve);
		}
	}
	printf("--------------------------------------------------------\n");
	fflush(stdout);
}

#define SHOW_PTR mysql_lve_mutex_governor_ptr?mysql_lve_mutex_governor_ptr->is_in_lve:-100

void hard_load() {
	long long i = 0, j = 0;
#ifdef DBG
	while(i<300000000) {
#else
	while (i < 6) {
#endif
		i++;
		j += cos(i) + abs(j) / 333;
	}
	fflush(stdout);
}

void hard_load2() {
	long long i = 0, j = 0;
	while (i < 2) {
		i++;
		j += cos(i) + abs(j) / 333;
	}
	fflush(stdout);
}

void task_pull_in_mutex() {
	pthread_mutex_t mtx1 = PTHREAD_MUTEX_INITIALIZER;
	pthread_mutex_t mtx2 = PTHREAD_MUTEX_INITIALIZER;
	pthread_mutex_t mtx3 = PTHREAD_MUTEX_INITIALIZER;

	my_pthread_lvemutex_lock(&mtx);
#ifdef DBG
	printf("Lock mutex A, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
	my_pthread_lvemutex_lock(&mtx2);
#ifdef DBG
	printf("Lock mutex B, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
	my_pthread_lvemutex_lock(&mtx3);
#ifdef DBG
	printf("Lock mutex C, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#else
	hard_load2();
#endif
	my_pthread_lvemutex_unlock(&mtx);
#ifdef DBG
	printf("UnLock mutex A, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
	my_pthread_lvemutex_unlock(&mtx2);
#ifdef DBG
	printf("UnLock mutex B, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
	my_pthread_lvemutex_unlock(&mtx1);
#ifdef DBG
	printf("UnLock mutex C, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
}

void task_pull_in_mutex2() {
	pthread_mutex_t mtx1 = PTHREAD_MUTEX_INITIALIZER;
	pthread_mutex_t mtx2 = PTHREAD_MUTEX_INITIALIZER;
	pthread_mutex_t mtx3 = PTHREAD_MUTEX_INITIALIZER;

	my_pthread_lvemutex_lock(&mtx1);
#ifdef DBG
	printf("Lock mutex A, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
	my_pthread_lvemutex_lock(&mtx2);
#ifdef DBG
	printf("Lock mutex B, %d\n", SHOW_PTR);
	fflush(stdout);

	//governor_setlve_mysql_thread_info(gettid());

	print_avail_thrs();
	sleep(10);
#endif
	my_pthread_lvemutex_lock(&mtx3);
#ifdef DBG
	printf("Lock mutex C, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#else
	hard_load2();
#endif
	my_pthread_lvemutex_unlock(&mtx1);
#ifdef DBG
	printf("UnLock mutex A, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
	my_pthread_lvemutex_unlock(&mtx2);
#ifdef DBG
	printf("UnLock mutex B, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
	my_pthread_lvemutex_unlock(&mtx1);
#ifdef DBG
	printf("UnLock mutex C, %d\n", SHOW_PTR);
	fflush(stdout);
	print_avail_thrs();
	sleep(10);
#endif
}

void *task(void *arg) {
	int ret;
#ifdef DBG
	printf("Thread started(ll)\n");
	print_avail_thrs();
	fflush(stdout);

	printf("Thread started %d, %d\n", gettid(), SHOW_PTR);
	fflush(stdout);
	//ret = send_info_begin("test1");
#endif	
	put_in_lve("test1");
#ifdef DBG
	print_avail_thrs();
	printf("Thread, in LVE, %d\n", SHOW_PTR);
	fflush(stdout);
#endif	
	hard_load();

	//sleep(30);
	task_pull_in_mutex2();
#ifdef DBG
	print_avail_thrs();
	printf("Prepareo for second mutex\n", SHOW_PTR);
	fflush(stdout);
	//governor_setlve_mysql_thread_info(gettid());
	//sleep(10);
#endif
	hard_load();
	task_pull_in_mutex();
#ifdef DBG
	print_avail_thrs();
#endif
	lve_thr_exit();
#ifdef DBG
	printf("Thread, out of LVE, %d\n", SHOW_PTR);
	fflush(stdout);
	//ret = send_info_end("test1");
	printf("Thread, send info\n");
	fflush(stdout);

	print_avail_thrs();
#endif

	return NULL;
}

pid_t getRandomPid() {
	pid_t pd = 0;
	if (mysql_lve_mutex_governor) {
		pthread_mutex_lock(&mtx_mysql_lve_mutex_governor_ptr);
		int counter = 0;
		HASH_SEARCH_STATE state;
		mysql_mutex *item;
		pid_t key;
		for (item = (mysql_mutex *) hash_first(mysql_lve_mutex_governor,
				(uchar*) &key, sizeof(pid_t), &state); item; item
				= (mysql_mutex *) hash_next(mysql_lve_mutex_governor,
						(uchar*) &key, sizeof(pid_t), &state)) {
			counter++;
		}

		if (counter > 0) {
			int fnd_pid_nmb = rand() % counter;
			item = hash_element(mysql_lve_mutex_governor, (ulong) fnd_pid_nmb);
			if (item) {
				pd = item->key;
			}
		}

		pthread_mutex_unlock(&mtx_mysql_lve_mutex_governor_ptr);

	}
	return pd;
}

void *task1(void *arg) {
	pid_t pd = 0;
#ifdef DBG
	printf("Started watcher\n");
	fflush(stdout);
#endif
	sleep(10);
	while (try <= TRYS_NMB) {
		pd = getRandomPid();
#ifdef DBG
		printf("Get random pid1 %d\n", pd);
		fflush(stdout);
#endif
		if (pd)
			governor_setlve_mysql_thread_info(pd);
		pd = 0;
		sleep(1);
	}
	return NULL;
}

int main() {
	//seteuid(498);
	printf("Main daemon started\n");
	pid_t pid = 0;
	int chld_state;

	config_init("../db-governor.xml.test");

	if (open_log("test1.log")) {
		printf("Can't open log file %d\n", errno);
	}
	if (open_restrict_log("test2.log")) {
		printf("Can't open restrict log file %d\n", errno);
		close_log();
	}
	print_config(get_config());

	/*pid = fork();
	 if (pid < 0) {
	 return -1;
	 }
	 if (pid > 0) {

	 init_tid_table();
	 dbgov_init();
	 //Work cycle
	 create_socket();

	 get_data_from_client(NULL);

	 waitpid(pid, &chld_state, 0);
	 printf("Main daemon restart child\n");
	 }
	 if (pid == 0) {*/
	close_log();
	close_restrict_log();
	//connect_to_server();
	load_lbr();
	governor_init_lve();
	init_bad_users_list_utility();
	//add_user_to_list("test1");
	pthread_t t2[1];
	pthread_create(&t2[0], NULL, task1, NULL);
	while (try < TRYS_NMB) {
		try++;
		if (try % 10000 == 1)
			printf("Try %d\n", try);
		fflush(stdout);
#ifdef DBG
		int rr = 1;//rand() % 10 + 1;
#else
		int rr = 100;
#endif
		pthread_t t1[rr];
		int i = 0;
		//printf("Try %d Will start %d\n", try, rr);
		//task(NULL);
		//task(NULL);
		for (i = 0; i < rr; i++) {
			if (i < rr) {
				if (pthread_create(&t1[i], NULL, task, NULL) != 0) {
					printf("Try %d - %d pthread_create() error\n", try, i);
				} //else {
				//    printf("Try %d - %d pthread_create()\n", try, i);
				//}
			}
		}
		for (i = 0; i < rr; i++) {
			pthread_join(t1[i], NULL);
		}
	}
	try++;
	pthread_join(t2[0], NULL);
	governor_destroy_lve();
	remove_bad_users_list_utility();
	//close_sock();
	//return 0;
	//}

	close_log();
	close_restrict_log();
	printf("Main daemon terminated\n");
	return 0;
}
