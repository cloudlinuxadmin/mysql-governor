/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#ifndef COMMANDS_H_
#define COMMANDS_H_

#include "data.h"
#include "governor_config.h"
#include "stats.h"

void reinit_command_list ();
void free_commands_list ();
void account_unrestrict (Account * ac);
void account_restrict (Account * ac, stats_limit_cfg * limit);
void send_commands_cycle ();
void send_commands (Command * cmd, void *data);
void *send_governor (void *data);
void restore_all_max_user_conn(MODE_TYPE debug_mode);

#endif /* COMMANDS_H_ */
