/* Copyright Cloud Linux Inc 2010-2011 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * db_governor application
 * author Igor Seletskiy <iseletsk@cloudlinux.com>
 * author Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 *
 */

#ifndef _USER_ACCOUNT_H_
#define _USER_ACCOUNT_H_ 1

#include <glib.h>
#include <stdlib.h>
#include <string.h>
#include "stats.h"
#include "data.h"

User_stats *add_user_stats (username_t account_id, GHashTable * accounts,
			    GHashTable * users);

struct user_account
{
  username_t username;
  username_t account;
};

void init_user_table ();
void free_user_table ();
struct user_account *get_user_account (username_t username);
int check_if_user_restricted (username_t username, GHashTable * accounts);

#endif
