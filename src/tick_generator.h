/*
 * tick_generator.h
 *
 *  Created on: Aug 8, 2012
 *      Author: alexey
 */

#ifndef TICK_GENERATOR_H_
#define TICK_GENERATOR_H_

void increment_tick ();
unsigned long long get_current_tick ();
int is_new_tick (long long tick);

#endif /* TICK_GENERATOR_H_ */
