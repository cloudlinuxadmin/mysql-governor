/*
 * governor_write_data.c
 *
 *  Created on: Aug 6, 2012
 *      Author: alexey
 */

#undef pthread_mutex_t
#undef pthread_mutex_lock
#undef pthread_mutex_unlock

#include <stdio.h>
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

#include <unistd.h>
#include <time.h>
#include <poll.h>

#include "data.h"

#include "governor_write_data.h"
#include "parce_proc_fs.h"
#include "dbgovernor_string_functions.h"
#include "shared_memory.h"

#define SEC2NANO 1000000000

pthread_mutex_t mtx_write = PTHREAD_MUTEX_INITIALIZER;
sock_data sd;

static int try_lock2(pthread_mutex_t *mtx) {
	int trys = 0, rc = 0;
	while (trys < 10) {
		rc = pthread_mutex_trylock(mtx);
		if (rc == 0)
			return 0;
		if (rc == EBUSY)
			trys++;
		else
			return -1;
	}
	return -1;
}

static int try_lock(pthread_mutex_t *mtx) {
	int rc = pthread_mutex_trylock(mtx);

	switch (rc) {
	case 0:
		break;
	case EBUSY: {
		struct timespec tim;

		clock_gettime(CLOCK_REALTIME, &tim);
		tim.tv_nsec += (double) 0.05 * (double) SEC2NANO;

		rc = pthread_mutex_timedlock(mtx, &tim);
		if (rc)
			return -1;
	}
		break;
	case EINVAL:
	default:
		rc = -1;
		break;
	}

	return rc;
}

static int close_sock_in();

pid_t gettid(void) {
	return syscall(__NR_gettid);
}

static int
connection_with_timeout_poll(int sk, struct sockaddr_un *sa,  socklen_t len, int timeout)
{
    int flags = 0, error = 0, ret = 0, error_len = sizeof(error), current_size = 0, index = 0;
    int nfds = 1;
    int ts;

    ts = timeout * 1000;
    struct pollfd fds[1];

    memset(fds, 0 , sizeof(fds));

    fds[0].fd = sk;
    fds[0].events= POLLIN;

    if( (flags = fcntl(sk, F_GETFL, 0)) < 0)
        return -1;

    if(fcntl(sk, F_SETFL, flags | O_NONBLOCK) < 0)
        return -1;

    if( (ret = connect(sk, (struct sockaddr *)sa, len)) < 0 )
        if (errno != EINPROGRESS)
            return -1;

    if(ret != 0){
    		int is_eintr = 0;
    		do{
    			if( (ret = poll(fds, nfds, ts)) < 0){
    				if (errno!=EINTR){
    					close(sk);
    					return -1;
    				}
    				is_eintr = 1;
    			} else {
    				is_eintr = 0;
    			}
    		} while (is_eintr);
    	    if(ret == 0){
    	    	close(sk);
    	        errno = ETIMEDOUT;
    	        return -1;
    	    } else if(fds[0].revents & POLLNVAL){
    	    	close(sk);
    	    	return -1;
    	    } else if (fds[0].revents & POLLHUP){
    	    	close(sk);
    	    	return -1;
    	    } else
#ifdef _GNU_SOURCE
    	    if (fds[0].revents & POLLHUP){
    	       	close(sk);
    	      	return -1;
    	    } else
#endif
    	    if (fds[0].revents & POLLERR){
    	       	close(sk);
    	       	return -1;
    	    } else if(fds[0].revents & POLLOUT){
    	    	if(getsockopt(sk, SOL_SOCKET, SO_ERROR, &error, &error_len) < 0){
    	    	   	close(sk);
    	    	    return -1;
    	    	}
    	    } else {
    	    	close(sk);
    	    	return -1;
    	    }

    	    if(error){
    	    	close(sk);
    	        errno = error;
    	        return -1;
    	    }
    }

    /*if(fcntl(sk, F_SETFL, flags) < 0) {
    	close(sk);
        return -1;
    }*/

    return 0;
}

static int
connection_with_timeout_select(int sk, struct sockaddr_un *sa,  socklen_t len, int timeout)
{
    int flags = 0, error = 0, ret = 0, error_len = sizeof(error);
    fd_set  read_set, write_set;
    struct timeval  ts;

    ts.tv_sec = timeout;
    ts.tv_usec = 0;

    FD_ZERO(&read_set);
    FD_SET(sk, &read_set);
    write_set = read_set;

    if( (flags = fcntl(sk, F_GETFL, 0)) < 0)
        return -1;

    if(fcntl(sk, F_SETFL, flags | O_NONBLOCK) < 0)
        return -1;

    if( (ret = connect(sk, (struct sockaddr *)sa, len)) < 0 )
        if (errno != EINPROGRESS)
            return -1;

    if(ret != 0){
    	    if( (ret = select(sk + 1, &read_set, &write_set, NULL, &ts)) < 0){
    	    	close(sk);
    	        return -1;
    	    }
    	    if(ret == 0){
    	    	close(sk);
    	        errno = ETIMEDOUT;
    	        return -1;
    	    }

    	    if (FD_ISSET(sk, &read_set) || FD_ISSET(sk, &write_set)){
    	        if(getsockopt(sk, SOL_SOCKET, SO_ERROR, &error, &error_len) < 0){
    	        	close(sk);
    	            return -1;
    	        }
    	    }else {
    	    	close(sk);
    	        return -1;
    	    }

    	    if(error){
    	    	close(sk);
    	        errno = error;
    	        return -1;
    	    }
    }

    /*if(fcntl(sk, F_SETFL, flags) < 0) {
    	close(sk);
        return -1;
    }*/

    return 0;
}

static int connect_to_server_in() {
	int s, len;
	struct sockaddr_un saun;
	sd.socket = 0;
	sd.status = 0;

	if ((s = socket(AF_UNIX, SOCK_STREAM, 0)) < 0) {
		return -1;
	}

	saun.sun_family = AF_UNIX;
	strncpy(saun.sun_path, MYSQL_SOCK_ADDRESS, sizeof(saun.sun_path)-1);

	len = sizeof(struct sockaddr_un);

	if (connection_with_timeout_poll(s, &saun, len, 5) < 0) {
		return -2;
	}
	/*int rt_code;
	rt_code = fcntl(s, F_GETFL, 0);
	fcntl(s, F_SETFL, rt_code | O_NONBLOCK);*/

	sd.socket = s;
	sd.status = 1;
	return 0;
}

int connect_to_server() {
	int ret = 0;
	pthread_mutex_lock(&mtx_write);
	ret = connect_to_server_in();
	pthread_mutex_unlock(&mtx_write);
	return ret;
}

int send_info(char *username, int type) {

	pid_t current_pid = getpid();
	pid_t current_tid = gettid();

	dbgov_proc_time item1;
	dbgov_iostat item2;

	get_proc_time(&item1, current_pid, current_tid);
	get_io_stat(&item2, current_pid, current_tid);

#ifdef TEST
	//printf("Prepare info PID %d TID %d CPU %lld R+W %lld\n", current_pid, current_tid, item1.stime + item1.utime, item2.read_bytes+item2.write_bytes);
#endif
	struct timespec tim;

	clock_gettime(CLOCK_REALTIME, &tim);

	client_data snd;
	snd.type = type;
	strlcpy(snd.username, username, sizeof(snd.username));
	snd.pid = current_pid;
	snd.tid = current_tid;
	snd.read = item2.read_bytes;
	snd.write = item2.write_bytes;
	snd.cpu = item1.stime + item1.utime;
	snd.update_time = tim.tv_sec;
	snd.naoseconds = tim.tv_nsec;

	if (try_lock(&mtx_write))
		return -1;
	/*if (!sd.status) {
		close(sd.socket);
		if (connect_to_server_in() < 0) {
			pthread_mutex_unlock(&mtx_write);
			return -1;
		}
	}*/
	//pthread_mutex_unlock(&mtx_write);

	//if (try_lock(&mtx_write)) return -1;
	if (send(sd.socket, &snd, sizeof(client_data), 0) != sizeof(client_data)) {
		//close_sock_in();
		pthread_mutex_unlock(&mtx_write);
		return -1;
	}
	pthread_mutex_unlock(&mtx_write);

	return 0;

}

int send_info_begin(char *username) {
#ifdef TEST
	//printf("Send begin info %s, %d, %d\n", username, sd.socket, sd.status);
#endif
	return send_info(username, 0);
}

int send_info_end(char *username) {
#ifdef TEST
	//printf("Send end info %s, %d, %d\n", username, sd.socket, sd.status);
#endif
	return send_info(username, 1);
}

static int close_sock_in() {
	if (sd.status) {
		close(sd.socket);
		sd.status = 0;
	}
	return 0;
}

int close_sock() {
	int rc = 0;
	pthread_mutex_lock(&mtx_write);
	rc = close_sock_in();
	pthread_mutex_unlock(&mtx_write);
	return rc;
}

sock_data *get_sock() {
	return &sd;
}

//LVE functions

void *lve_library_handle = NULL;
void *lve = NULL;

void * (*init_lve)(void *, void *) = NULL;
int (*destroy_lve)(void *) = NULL;
int (*lve_enter_flags)(void *, uint32_t, uint32_t *, int) = NULL;
int (*lve_exit)(void *, uint32_t *) = NULL;
int (*lve_enter_pid) (void *, uint32_t, pid_t) = NULL;

void *governor_load_lve_library() {
	lve_library_handle = NULL;

	char *error_dl = NULL;
	lve_library_handle = dlopen("liblve.so.0", RTLD_LAZY);
	if (lve_library_handle) {
		while (1) {
			init_lve = (void* (*)(void *, void *)) dlsym(lve_library_handle,
					"init_lve");
			if ((error_dl = dlerror()) != NULL) {
				init_lve = NULL;
				destroy_lve = NULL;
				lve_enter_flags = NULL;
				lve_exit = NULL;
				lve_enter_pid = NULL;
				break;
			}
			destroy_lve = (int(*)(void *)) dlsym(lve_library_handle,
					"destroy_lve");
			if ((error_dl = dlerror()) != NULL) {
				init_lve = NULL;
				destroy_lve = NULL;
				lve_enter_flags = NULL;
				lve_exit = NULL;
				lve_enter_pid = NULL;
				break;
			}
			lve_enter_flags
					= (int(*)(void *, uint32_t, uint32_t *, int)) dlsym(
							lve_library_handle, "lve_enter_flags");
			if ((error_dl = dlerror()) != NULL) {
				init_lve = NULL;
				destroy_lve = NULL;
				lve_enter_flags = NULL;
				lve_exit = NULL;
				lve_enter_pid = NULL;
				break;
			}
			lve_exit = (int(*)(void *, uint32_t *)) dlsym(lve_library_handle,
					"lve_exit");
			if ((error_dl = dlerror()) != NULL) {
				init_lve = NULL;
				destroy_lve = NULL;
				lve_enter_flags = NULL;
				lve_exit = NULL;
				lve_enter_pid = NULL;
				break;
			}
			lve_enter_pid = (int(*)(void *, uint32_t, pid_t)) dlsym(lve_library_handle,
					"lve_enter_pid");
			if ((error_dl = dlerror()) != NULL) {
				init_lve = NULL;
				destroy_lve = NULL;
				lve_enter_flags = NULL;
				lve_exit = NULL;
				lve_enter_pid = NULL;
				break;
			}
			break;
		}

	} else {
		return NULL;
	}
	if (!lve_exit)
		return NULL;
	return lve_library_handle;
}

int governor_init_lve() {
	if (init_lve) {
		if (lve == NULL) {
			lve = init_lve(malloc, NULL);
		}
	}
	if (lve == NULL) {
		return -1;
	}
	init_bad_users_list_client();
	return 0;
}

void governor_destroy_lve() {
	if (destroy_lve && lve) {
		destroy_lve(lve);
	}
	if (lve_library_handle) {
		dlclose(lve_library_handle);
	}
	remove_bad_users_list_client();
}

__thread uint32_t lve_uid = 0;

int governor_enter_lve(uint32_t *cookie, char *username) {
	lve_uid = 0;
	int container_lve = is_user_in_bad_list_cleint_persistent(username);
	if (container_lve && lve_enter_flags
			&& lve) {
                errno = 0;
		int rc = lve_enter_flags(lve, container_lve, cookie, ((int) ((1 << 2) | (1
				<< 3)))); //LVE_NO_MAXENTER|LVE_SILENCE
		int keep_errno = errno;
		if (rc) {
			if (keep_errno == EPERM) { //if already inside LVE
				//lve_exit(lve, cookie);
				//return -1;
				return 0;
			}

			return -1;
		}
		lve_uid = container_lve;
		return 0;
	}
	return 1;
}

int governor_enter_lve_light(uint32_t *cookie) {
	if (lve_enter_flags && lve && lve_uid) {
                errno = 0;
		int rc = lve_enter_flags(lve, lve_uid, cookie, ((int) ((1 << 2) | (1
				<< 3)))); //LVE_NO_MAXENTER|LVE_SILENCE
		int keep_errno = errno;
		if (rc) {
			if (keep_errno == EPERM) { //if already inside LVE
				//lve_exit(lve, cookie);
				//return -1;
                                return 0;
			}

			return -1;
		}
		return 0;
	}
	return 1;
}

void governor_lve_exit(uint32_t *cookie) {
	if (lve_exit && lve)
		lve_exit(lve, cookie);
}

void governor_lve_exit_null() {
	uint32_t lcookie=0;
	if (lve_exit)
		lve_exit(NULL, &lcookie);
}

int governor_lve_enter_pid(pid_t pid){
	if(lve_enter_pid){
	    if(lve_enter_pid(lve, BAD_LVE, pid)) return -1;
	}
	return 0;
}

int governor_lve_enter_pid_user(pid_t pid, char *username){
	if(lve_enter_pid && username){
		int container_lve = is_user_in_bad_list_cleint_persistent(username);
		if(container_lve){
			if(lve_enter_pid(lve, container_lve, pid)) return -1;
		}
	}
	return 0;
}


