/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Shkatula Pavel <shpp@cloudlinux.com>
 */

#include <stdio.h>

#include "data.h"
#include "xml.h"

#include "dbctl_cfg.h"
#include "dbctl_rest.h"
#include "dbctl_conn.h"
#include "wrappers.h"
#include "dbgovernor_string_functions.h"

int restrict_user(char *user, char *level) {
	FILE *inout = NULL;
	int _socket = -1;

	if (!strncmp(user, "default", sizeof(username_t) - 1)) {
		return 1;
	}

	if (opensock_to_server_dbctl(&_socket, &inout)) {
		client_type_t ctt = DBCTL;
		fwrite(&ctt, sizeof(client_type_t), 1, inout);
		fflush(inout);

		DbCtlCommand command;
		command.command = RESTRICT;
		strcpy(command.parameter, "");
		strncpy(command.options.username, user,
				sizeof(command.options.username) - 1);
		command.options.cpu = 0;
		command.options.level = atoi((level ? level : "-1"));
		command.options.read = 0;
		command.options.write = 0;
		command.options.timeout = 0;
		command.options.user_max_connections = 0;

		fwrite_wrapper(&command, sizeof(DbCtlCommand), 1, inout);
		fflush(inout);

		closesock_to_server_dbctl(_socket, inout);
	} else {

		closesock_to_server_dbctl(_socket, inout);
		return 0;
	}

	return 1;
}

int unrestrict(char *user) {
	FILE *inout = NULL;
	int _socket = -1;

	if (!strncmp(user, "default", sizeof(username_t) - 1)) {
		return 1;
	}

	if (opensock_to_server_dbctl(&_socket, &inout)) {
		client_type_t ctt = DBCTL;
		fwrite(&ctt, sizeof(client_type_t), 1, inout);
		fflush(inout);

		DbCtlCommand command;
		command.command = UNRESTRICT;
		strcpy(command.parameter, "");
		strncpy(command.options.username, user,
				sizeof(command.options.username) - 1);
		command.options.cpu = 0;
		command.options.level = 0;
		command.options.read = 0;
		command.options.write = 0;
		command.options.timeout = 0;
		command.options.user_max_connections = 0;

		fwrite_wrapper(&command, sizeof(DbCtlCommand), 1, inout);
		fflush(inout);

		closesock_to_server_dbctl(_socket, inout);
	} else {
		closesock_to_server_dbctl(_socket, inout);
		return 0;
	}

	return 1;
}

int dbupdatecmd(void) {
	FILE *inout = NULL;
	int _socket = -1;

	if (opensock_to_server_dbctl(&_socket, &inout)) {
		client_type_t ctt = DBCTL;
		fwrite(&ctt, sizeof(client_type_t), 1, inout);
		fflush(inout);

		DbCtlCommand command;
		command.command = DBUSER_MAP_CMD;
		strcpy(command.parameter, "");
		strcpy(command.options.username, "");
		command.options.cpu = 0;
		command.options.level = 0;
		command.options.read = 0;
		command.options.write = 0;
		command.options.timeout = 0;
		command.options.user_max_connections = 0;

		fwrite_wrapper(&command, sizeof(DbCtlCommand), 1, inout);
		fflush(inout);

		closesock_to_server_dbctl(_socket, inout);
	} else {
		closesock_to_server_dbctl(_socket, inout);
		return 0;
	}

	return 1;
}

int unrestrict_all(void) {
	FILE *inout = NULL;
	int _socket = -1;

	if (opensock_to_server_dbctl(&_socket, &inout)) {
		client_type_t ctt = DBCTL;
		fwrite(&ctt, sizeof(client_type_t), 1, inout);
		fflush(inout);

		DbCtlCommand command;
		command.command = UNRESTRICT_A;
		strcpy(command.parameter, "");
		strcpy(command.options.username, "");
		command.options.cpu = 0;
		command.options.level = 0;
		command.options.read = 0;
		command.options.write = 0;
		command.options.timeout = 0;
		command.options.user_max_connections = 0;

		fwrite_wrapper(&command, sizeof(DbCtlCommand), 1, inout);
		fflush(inout);

		closesock_to_server_dbctl(_socket, inout);
	} else {
		closesock_to_server_dbctl(_socket, inout);
		return 0;
	}

	return 1;
}
