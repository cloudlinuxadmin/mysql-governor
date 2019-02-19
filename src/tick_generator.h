/*
 * Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
 *
 * Licensed under CLOUD LINUX LICENSE AGREEMENT
 * http://cloudlinux.com/docs/LICENSE.TXT
 *
 * Author: Alexey Berezhok <alexey.berezhok@cloudlinux.com>
 */

#ifndef TICK_GENERATOR_H_
#define TICK_GENERATOR_H_

void increment_tick ();
unsigned long long get_current_tick ();
int is_new_tick (long long tick);

#endif /* TICK_GENERATOR_H_ */
