/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Shkatula Pavel <shpp@cloudlinux.com>
 */


#ifndef __DBCTL_CONN__
#define __DBCTL_CONN__

int opensock_to_server_dbctl (int *_socket, FILE ** inout);
void closesock_to_server_dbctl (int _socket, FILE * inout);

#endif /* __DBCTL_CONN__ */
