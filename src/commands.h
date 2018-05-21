/*
 * commands.h
 *
 *  Created on: Aug 9, 2012
 *      Author: alexey
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

#endif /* COMMANDS_H_ */
