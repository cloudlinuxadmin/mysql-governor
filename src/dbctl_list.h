/* Copyright Cloud Linux Inc 2010-2012 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * dbctl_list.h
 *
 *  Created on: Oct 23, 2012
 *      Author: Shkatula Pavel
 *      E-mail: shpp@cloudlinux.com
 */


#ifndef __DBCTL_LIST__
#define __DBCTL_LIST__

void list(int flag, int non_priv);
void list_restricted(void);
void show_uids(void);
void list_restricted_shm(void);

#endif /* __DBCTL_LIST__ */
