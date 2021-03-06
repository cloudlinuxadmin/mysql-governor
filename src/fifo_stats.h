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

#ifndef _FIFO_STATS_H_
#define _FIFO_STATS_H_ 1

#include <stdlib.h>
#include "data.h"

struct fifo_stats
{
  Stats **ar;
  int size;
  int first;
};

struct fifo_stats *fifo_stats_init (int size);
void fifo_stats_free (struct fifo_stats *fifo);
Stats *fifo_stats_push (struct fifo_stats *fifo, Stats * x);
Stats *fifo_stats_get (struct fifo_stats *fifo, int i);
void fifo_stats_foreach (struct fifo_stats *fifo, void (*fp) (Stats *));
Stats *fifo_stats_refresh_last (struct fifo_stats *fifo, Stats * x);

#endif
