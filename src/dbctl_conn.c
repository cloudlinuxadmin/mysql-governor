/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Shkatula Pavel <shpp@cloudlinux.com>
 */

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>

#include <string.h>
#include <math.h>
#include <glib.h>

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>

#include "data.h"
#include "dbctl_conn.h"

int
connect_to_server_dbctl (void)
{
	int s;
	socklen_t len;
	struct sockaddr_un saun;

	if ((s = socket (AF_UNIX, SOCK_STREAM, 0)) < 0)
	{
		return -1;
	}

	saun.sun_family = AF_UNIX;
	strcpy (saun.sun_path, SOCK_ADDRESS);

	if (connect (s, (struct sockaddr *) &saun, sizeof saun) < 0)
	{
		close (s);
		return -2;
	}

	return s;
}

int
opensock_to_server_dbctl (int *_socket, FILE **inout)
{
	int s = connect_to_server_dbctl ();
	if (s < 0)
	{
		fprintf(stderr, "Can't connect to dbctl server(%s) - errno %d; Maybe governor is not started\n",
				SOCK_ADDRESS, errno);
		return 0;
	}

	FILE *fptr = fdopen (s, "r+");
	if (!fptr)
	{
		fprintf(stderr, "fdopen to dbctl server(%s) failed - errno %d\n", SOCK_ADDRESS, errno);
		close(s);
		return 0;
	}

	*_socket = s;
	*inout = fptr;
	return 1;
}

void
closesock_to_server_dbctl (int _socket, FILE * inout)
{
	if (inout)
	{
		fclose (inout);
	}
	else if (_socket > 0)
	{
		close (_socket);
	}
}
