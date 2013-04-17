/*
 * lock_testing.c
 *
 *  Created on: Sep 20, 2012
 *      Author: Alexey Berezhok
 *		E-mail: alexey_com@ukr.net
 */

//THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS," AND COPYRIGHT HOLDERS
//MAKE NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT
//LIMITED TO, WARRANTIES OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE
//OR THAT THE USE OF THE SOFTWARE OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD
//PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.
//COPYRIGHT HOLDERS WILL NOT BE LIABLE FOR ANY DIRECT, INDIRECT, SPECIAL OR
//CONSEQUENTIAL DAMAGES ARISING OUT OF ANY USE OF THE SOFTWARE OR DOCUMENTATION.
#include <stdio.h>
#include <stdint.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/un.h>
#include <stdlib.h>
#include <string.h>
#include <sys/syscall.h>
#include <linux/unistd.h>
#include <pthread.h>
#include <fcntl.h>
#include <dlfcn.h>
#include <errno.h>

pthread_mutex_t mtx_write = PTHREAD_MUTEX_INITIALIZER;
float data = 0;

static int try_lock(pthread_mutex_t *mtx) {
	int trys = 0, rc = 0;
	while (trys < 10) {
		rc = pthread_mutex_trylock(mtx);
		if (rc == 0)
			return 0;
		if (rc == EBUSY)
			trys++;
		else
			return -1;
		sleep(1);
	}
	return -1;
}

void * send_info(void *dt) {
	intptr_t t = (intptr_t) dt;
	printf("Thread %d data %f\n", t, data);
	if (try_lock(&mtx_write))
		return NULL;
	if (data == 0)
		data = t;
	pthread_mutex_unlock(&mtx_write);

	if (try_lock(&mtx_write))
		return NULL;
	printf("Thread %d data %f\n", t, data);
	if(rand()%10==0){
		data = 0;
	}
	pthread_mutex_unlock(&mtx_write);

	return 0;

}

void *task1(void *arg) {
	if (try_lock(&mtx_write)) {
		printf("Lock from task1 failed\n");
		return NULL;
	}
	printf("Lock from task1 - locked\n");
	data = 1.0;
	sleep(5);
	pthread_mutex_unlock(&mtx_write);
	printf("Lock from task1 - unlocked\n");
	return NULL;
}

void *task2(void *arg) {
	if (try_lock(&mtx_write)) {
		printf("Lock from task2 failed\n");
		return NULL;
	}
	printf("Lock from task2 - locked\n");
	data = 2.0;
	sleep(5);
	pthread_mutex_unlock(&mtx_write);
	printf("Lock from task2 - unlocked\n");
	return NULL;
}

int main() {
	pthread_t t1[10000];
	intptr_t i = 0;
	for (i = 0; i < 10000; i++) {
		int res = pthread_create(&t1[i], NULL, send_info, (void *) i);
		if(res!=0) {
			printf("Therad %d error creation\n", i);
			t1[i]=0;
		}
	}
	for (i = 0; i < 10000; i++) {
		if(t1[i]) pthread_join(t1[i], NULL);
	}

	return 0;
}
