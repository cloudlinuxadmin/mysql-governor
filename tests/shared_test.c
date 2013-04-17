/*
 * shared_test.c
 *
 *  Created on: Sep 10, 2012
 *      Author: alexey
 */

#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

#include "../src/shared_memory.h"

int main() {

	pid_t pid = fork();

	if (pid == 0) {
		printf("init shared memory\n");
		init_bad_users_list();

		add_user_to_list("pepelac1");
		add_user_to_list("pepelac2");
		add_user_to_list("pepelac3");
		add_user_to_list("pepelac4");
		add_user_to_list("pepelac5");

		printf_bad_users_list();

		sleep(10);

		printf("Add existing user pepelac 4\n");

		add_user_to_list("pepelac4");
		printf_bad_users_list();

		printf("Delete user pepelac 4\n");

		delete_user_from_list("pepelac4");
		printf_bad_users_list();

		sleep(10);

		printf("Delete all users\n");

		delete_user_from_list("pepelac1");
		delete_user_from_list("pepelac2");
		delete_user_from_list("pepelac3");
		delete_user_from_list("pepelac5");
		printf_bad_users_list();

		sleep(10);

		remove_bad_users_list();
	} else {

		setuid(500);
		setgid(500);
		printf("Is peplac4 in list %d\n", is_user_in_bad_list_cleint("pepelac4"));
		sleep(3);
		printf("Is peplac4 in list %d\n", is_user_in_bad_list_cleint("pepelac4"));
		sleep(10);
		printf("Is peplac4 in list %d\n", is_user_in_bad_list_cleint("pepelac4"));
		sleep(10);
		printf("Is peplac4 in list %d\n", is_user_in_bad_list_cleint("pepelac4"));
	}
	return 0;
}
