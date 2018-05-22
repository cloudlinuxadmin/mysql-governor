/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_list.h
 *
 *  Created on: Oct 24, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
 */


#ifndef __DBCTL_CONN__
#define __DBCTL_CONN__

int opensock(int *_socket, FILE **in, FILE **out);
void closesock(int _socket, FILE *in, FILE *out);

#endif /* __DBCTL_CONN__ */
