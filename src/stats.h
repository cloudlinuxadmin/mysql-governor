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

#ifndef _STATS_H_
#define _STATS_H_ 1

#include <glib.h>
#include <stdlib.h>
#include "data.h"
#include "fifo_stats.h"

#include <unistd.h>
#include <sys/time.h>

#define REFRESH_TIME_SEC 1
#define REFRESH_TIME_USEC 0


typedef struct account_stats_average
{
  Stats sum_statistics;
  long count;
} StatsAverage;

typedef struct account_struct
{
  char *id;
  GPtrArray *users;
  Stats current;
  Stats long_average;
  Stats mid_average;
  Stats short_average;

  int restricted;
  int timeout;
  time_t start_count;
  restrict_info info;
  int need_dbg;

} Account;

Account *init_account (char *id);
void free_account (gpointer ignored, Account * ac);

typedef struct timeval _timeval;

typedef struct user_stats_struct
{
  const char *id;
  Account *account;
  struct fifo_stats *stats;
  Stats long_average;
  Stats mid_average;
  Stats short_average;
  long long tick;
} User_stats;

User_stats *init_user_stats (const char *id, Account * ac);
void free_user_stats (gpointer ignored, User_stats * us);

const int LONG_SIZE;
const int SHORT_SIZE;
const int MID_SIZE;


/* add two stats records */
void sum_stats (Stats * dest, Stats * nr);

/* add stats record to user */
Stats *push_stats (Stats * st, User_stats * us);

/* resets stat */
void reset_stats (Stats * st);

Stats *
refresh_stats(Stats * st, User_stats * us);

#endif
