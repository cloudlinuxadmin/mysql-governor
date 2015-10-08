/*
 * shared_memory.c
 *
 *  Created on: Sep 10, 2012
 *      Author: alexey
 */

#include <fcntl.h>
#include <sys/stat.h>
#include <errno.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <semaphore.h>
#include <pthread.h>

#include "data.h"
#include "dbgovernor_string_functions.h"
#include "shared_memory.h"
#include "dbuser_map.h"

#define MAX_ITEMS_IN_TABLE 100000
#define SHARED_MEMORY_NAME "governor_bad_users_list"
#define SHARED_MEMORY_SEM "governor_bad_users_list_sem"

typedef struct __items_structure {
    char username[USERNAMEMAXLEN];
    int32_t uid;
} items_structure;

typedef struct __shm_structure {
	long numbers;
	items_structure items[MAX_ITEMS_IN_TABLE];
} shm_structure;

shm_structure *bad_list = NULL;
int shm_fd = 0;
sem_t *sem = NULL;

int init_bad_users_list_utility() {

	if ((shm_fd = shm_open(SHARED_MEMORY_NAME, (O_RDWR), 0755))
			< 0) {
		return -1;
	}

	if ((bad_list = (shm_structure *) cl_mmap(0, sizeof(shm_structure), (PROT_READ
									| PROT_WRITE), MAP_SHARED, shm_fd, 0)) == MAP_FAILED) {
		close(shm_fd);
		return -1;
	}

	sem = sem_open(SHARED_MEMORY_SEM, O_CREAT, 0777, 1);

	if (sem == SEM_FAILED) {
		cl_munmap((void *) bad_list, sizeof(shm_structure));
		close(shm_fd);
		return -1;
	}
	if (sem_wait(sem) == 0) {
		clear_bad_users_list();
		sem_post(sem);
	}

	return 0;
}

int remove_bad_users_list_utility() {
	if (sem != SEM_FAILED) sem_close(sem);
	if (bad_list && (bad_list!= MAP_FAILED)) cl_munmap((void *) bad_list, sizeof(shm_structure));
	close(shm_fd);
	return 0;
}

int init_bad_users_list() {
	//shm_unlink(SHARED_MEMORY_NAME);
	sem_unlink(SHARED_MEMORY_SEM);
	mode_t old_umask = umask(0);

	int first = 0;
	if ((shm_fd = shm_open(SHARED_MEMORY_NAME, (O_CREAT | O_EXCL | O_RDWR),
							0755)) > 0) {
		first = 1;
	} else if ((shm_fd = shm_open(SHARED_MEMORY_NAME, (O_CREAT | O_RDWR), 0755))
			< 0) {
		umask(old_umask);
		return -1;
	}

	if (first) {
		ftruncate(shm_fd, sizeof(shm_structure));
	}

	if ((bad_list = (shm_structure *) cl_mmap(0, sizeof(shm_structure), (PROT_READ
									| PROT_WRITE), MAP_SHARED, shm_fd, 0)) == MAP_FAILED) {
		close(shm_fd);
		umask(old_umask);
		return -1;
	}

	sem = sem_open(SHARED_MEMORY_SEM, O_CREAT, 0777, 1);
	umask(old_umask);

	if (sem == SEM_FAILED) {
		cl_munmap((void *) bad_list, sizeof(shm_structure));
		close(shm_fd);
		return -1;
	}
	if (sem_wait(sem) == 0) {
		clear_bad_users_list();
		sem_post(sem);
	}

	return 0;
}

int init_bad_users_list_if_not_exitst(){
	if (!bad_list || (bad_list == MAP_FAILED)){
		return init_bad_users_list();
	}
	return 0;
}

void clear_bad_users_list() {
	if (!bad_list || (bad_list == MAP_FAILED))
	return;
	memset((void *) bad_list, 0, sizeof(shm_structure));
}

int remove_bad_users_list() {
	if (sem != SEM_FAILED) sem_close(sem);
	sem_unlink(SHARED_MEMORY_SEM);
	if (bad_list && (bad_list!= MAP_FAILED)) cl_munmap((void *) bad_list, sizeof(shm_structure));
	close(shm_fd);
	return 0;
}

int is_user_in_list(char *username) {
	if (!bad_list || (bad_list == MAP_FAILED))
	return -1;
	long index;
	for (index = 0; index < bad_list->numbers; index++) {
        if (!strncmp(bad_list->items[index].username, username, USERNAMEMAXLEN))
		return 1;
	}
	return 0;
}

int add_user_to_list(char *username, int is_all) {
	if (!bad_list || (bad_list == MAP_FAILED))
	return -1;
	int uid = BAD_LVE;
	if( lock_read_map() == 0 )
	{
	  uid=get_uid(username);
	  unlock_rdwr_map();
	}
	if(is_all && uid == BAD_LVE ){
		uid = 0;
	}
	if (!is_user_in_list(username)) {
		if ((bad_list->numbers + 1) == MAX_ITEMS_IN_TABLE)
		return -2;
		if (sem_wait(sem) == 0) {
			strlcpy(bad_list->items[bad_list->numbers].username, username,
					USERNAMEMAXLEN);
            bad_list->items[bad_list->numbers++].uid = uid;
			sem_post(sem);
		}
	}
	return 0;
}

int delete_user_from_list(char *username) {
	if (!bad_list || (bad_list == MAP_FAILED))
	return -1;
	long index;
	for (index = 0; index < bad_list->numbers; index++) {
		if (!strncmp(bad_list->items[index].username, username, USERNAMEMAXLEN)) {
			if (sem_wait(sem) == 0) {
				if (index == (bad_list->numbers - 1)) {
					bad_list->numbers--;
					sem_post(sem);
					return 0;
				} else {
					memmove( 
                             bad_list->items + index, 
                             bad_list->items + (index + 1),
							 sizeof( items_structure ) * (bad_list->numbers - index - 1)
                           );

					bad_list->numbers--;
					sem_post(sem);
					return 0;
				}
				sem_post(sem);
			}
		}
	}
	return -2;
}

int delete_allusers_from_list() {
	if (!bad_list || (bad_list == MAP_FAILED))
	return -1;
	if (sem_wait(sem) == 0) {
		clear_bad_users_list();
		sem_post(sem);
		return 0;
	}
	return -2;
}

long get_users_list_size() {
	if (!bad_list || (bad_list == MAP_FAILED) )
	return 0;
	return bad_list->numbers;
}

void printf_bad_users_list() {
	if (!bad_list || (bad_list == MAP_FAILED) )
	return;
	long index;
	for (index = 0; index < bad_list->numbers; index++) {
		printf("%ld) user - %s, uid - %d\n", index, bad_list->items[index].username, bad_list->items[index].uid);
	}
	return;
}


int32_t is_user_in_bad_list_cleint(char *username) {
	int shm_fd_clents = 0;
	int32_t fnd = 0;
	shm_structure *bad_list_clents;
	if ((shm_fd_clents = shm_open(SHARED_MEMORY_NAME, O_RDONLY, 0755)) < 0) {
		return 0;
	}
	if ((bad_list_clents = (shm_structure *) cl_mmap(0, sizeof(shm_structure),
			PROT_READ, MAP_SHARED, shm_fd_clents, 0)) == MAP_FAILED) {
		close(shm_fd_clents);
		return 0;
	}

	sem_t *sem_client = sem_open(SHARED_MEMORY_SEM, 0, 0777, 1);
	int trys = 1, sem_reopen = 0;

	if (sem_client != SEM_FAILED) {
		while (trys) {
			if (sem_trywait(sem_client) == 0) {
				if (bad_list_clents) {
					long index;
					for (index = 0; index < bad_list_clents->numbers; index++) {
						if (!strncmp(bad_list_clents->items[index].username, username,
								USERNAMEMAXLEN)) {
							fnd = bad_list_clents->items[index].uid;
							break;
						}
					}
				}
				trys = 0;
			} else {
				if (errno == EAGAIN) {
					trys++;
					if (trys == 100) {
						trys = 1;
						sem_close(sem_client);
						sem_client = sem_open(SHARED_MEMORY_SEM, 0, 0777, 1);
						sem_reopen++;
						if (sem_reopen==4) break;
					}
				} else {
					trys = 0;
				}

			}
		}
		sem_post(sem_client);
		sem_close(sem_client);
	}

	cl_munmap((void *) bad_list_clents, sizeof(shm_structure));
	close(shm_fd_clents);
	return fnd;
}

int user_in_bad_list_cleint_show() {
	int shm_fd_clents = 0;
	int fnd = 0;
	mode_t old_umask = umask(0);
	shm_structure *bad_list_clents;
	if ((shm_fd_clents = shm_open(SHARED_MEMORY_NAME, O_RDONLY, 0755)) < 0) {
		umask(old_umask);
		return 0;
	}
	if ((bad_list_clents = (shm_structure *) cl_mmap(0, sizeof(shm_structure),
			PROT_READ, MAP_SHARED, shm_fd_clents, 0)) == MAP_FAILED) {
		close(shm_fd_clents);
		umask(old_umask);
		return 0;
	}

	sem_t *sem_client = sem_open(SHARED_MEMORY_SEM, 0, 0777, 1);
	umask(old_umask);
	int trys = 1;

	if (sem_client != SEM_FAILED) {
		while (trys) {
			if (sem_trywait(sem_client) == 0) {
				if (bad_list_clents) {
					long index;
					for (index = 0; index < bad_list_clents->numbers; index++) {
						printf("%s\n", bad_list_clents->items[index].username);
					}
				}
				trys = 0;
			} else {
				if (errno == EAGAIN) {
					trys++;
					if (trys == 100) {
						trys = 1;
						sem_post(sem_client);
						sem_client = sem_open(SHARED_MEMORY_SEM, 0, 0777, 1);
					}
				} else {
					trys = 0;
				}

			}
		}
		sem_post(sem_client);
		sem_close(sem_client);
	}

	cl_munmap((void *) bad_list_clents, sizeof(shm_structure));
	close(shm_fd_clents);
	return fnd;
}

int shm_fd_clents_global = 0;
shm_structure *bad_list_clents_global = NULL;
pthread_mutex_t mtx_shared = PTHREAD_MUTEX_INITIALIZER;

int init_bad_users_list_client() {
	pthread_mutex_lock(&mtx_shared);
	if ((shm_fd_clents_global = shm_open(SHARED_MEMORY_NAME, O_RDONLY, 0755))
			< 0) {
		pthread_mutex_unlock(&mtx_shared);
		return -1;
	}
	if ((bad_list_clents_global = (shm_structure *) cl_mmap(0,
			sizeof(shm_structure), PROT_READ, MAP_SHARED, shm_fd_clents_global,
			0)) == MAP_FAILED) {
		close(shm_fd_clents_global);
		pthread_mutex_unlock(&mtx_shared);
		return -2;
	}
	pthread_mutex_unlock(&mtx_shared);

	return 0;
}

int remove_bad_users_list_client() {
	pthread_mutex_lock(&mtx_shared);
	if (bad_list_clents_global && (bad_list_clents_global != MAP_FAILED))
		cl_munmap((void *) bad_list_clents_global, sizeof(shm_structure));
	close(shm_fd_clents_global);
	pthread_mutex_unlock(&mtx_shared);
	return 0;
}

int32_t is_user_in_bad_list_cleint_persistent(char *username) {
	sem_t *sem_client = sem_open(SHARED_MEMORY_SEM, 0, 0777, 1);
	int trys = 1, sem_reopen = 0;
	int32_t fnd = 0;

	if (sem_client != SEM_FAILED) {
		while (trys) {
			if (sem_trywait(sem_client) == 0) {
				if (bad_list_clents_global && (bad_list_clents_global != MAP_FAILED)) {
					long index = 0;
					for (index = 0; index < bad_list_clents_global->numbers; index++) {
						if (!strncmp(bad_list_clents_global->items[index].username,
								username, USERNAMEMAXLEN)) {
							fnd = bad_list_clents_global->items[index].uid;
							break;
						}
					}
				}
				trys = 0;
			} else {
				if (errno == EAGAIN) {
					trys++;
					if (trys == 100) {
						trys = 1;
						sem_close(sem_client);
						sem_client = sem_open(SHARED_MEMORY_SEM, 0, 0777, 1);
						sem_reopen++;
						if (sem_reopen==4) break;
					}
				} else {
					trys = 0;
				}

			}
		}
		sem_post(sem_client);
		sem_close(sem_client);
	}

	return fnd;
}

void printf_bad_list_cleint_persistent(void) {
	printf( " USER             NUMBER\n" );
	sem_t *sem_client = sem_open(SHARED_MEMORY_SEM, 0, 0777, 1);
	int trys = 1, sem_reopen = 0;

	if (sem_client != SEM_FAILED) {
		while (trys) {
			if (sem_trywait(sem_client) == 0) {
				if (bad_list_clents_global && (bad_list_clents_global != MAP_FAILED)) {
					long index = 0;
					for (index = 0; index < bad_list_clents_global->numbers; index++) {
						printf( " %-16s %ld\n",
								bad_list_clents_global->items[index].username,
						        index);
					}
				}
				trys = 0;
			} else {
				if (errno == EAGAIN) {
					trys++;
					if (trys == 100) {
						trys = 1;
						sem_close(sem_client);
						sem_client = sem_open(SHARED_MEMORY_SEM, 0, 0777, 1);
						sem_reopen++;
						if (sem_reopen==4) break;
					}
				} else {
					trys = 0;
				}

			}
		}
		sem_post(sem_client);
		sem_close(sem_client);
	}

	return;
}
