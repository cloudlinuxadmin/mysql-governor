/*
 * tick_generator.c
 *
 *  Created on: Aug 8, 2012
 *      Author: alexey
 */

#include "tick_generator.h"

unsigned long long tick_id = 0;

void
increment_tick ()
{
  tick_id++;
}

unsigned long long
get_current_tick ()
{
  return tick_id;
}

int
is_new_tick (long long tick)
{
  if (tick != tick_id)
    return 1;
  else
    return 0;
}
