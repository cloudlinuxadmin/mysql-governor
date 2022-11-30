/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Shkatula Pavel <shpp@cloudlinux.com>
 */

#ifndef __DBCTL_LIST__
#define __DBCTL_LIST__

int list_all (int flag, int non_priv, int raw);
int list_all_json (int flag);
int list_restricted (void);
void show_uids (void);
void list_restricted_shm (void);

#endif /* __DBCTL_LIST__ */
