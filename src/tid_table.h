/*
 * tid_table.h
 *
 *  Created on: Aug 2, 2012
 *      Author: alexey
 */

#ifndef TID_TABLE_H_
#define TID_TABLE_H_

#include "data.h"

typedef struct __cnt_user_threads
{
  char username[USERNAMEMAXLEN];
  int max_simultaneous_requests;
} cnt_user_threads;

typedef struct __tid_table
{
  char username[USERNAMEMAXLEN];
  long long cpu;
  long long read;
  long long write;
  time_t update_time;
  long naoseconds;
  pid_t pid;
  int fd;
} tid_table;

typedef struct __Stat_counters
{
  Stats s;
  double tm;
} Stat_counters;

void free_tid (gpointer ti);
void free_tid_key (gpointer ti);
int init_tid_table ();
void free_tid_table ();
void add_new_tid_data (client_data * tbl, int fd);
tid_table *get_tid_data (pid_t tid, tid_table * buf);
void remove_tid_data (pid_t tid);
void proceed_tid_data (GHFunc func, gpointer user_data);
void add_new_tid_data2 (pid_t tid, tid_table * tbl);
void remove_tid_data_by_fd (int fd);
void reset_counters (char *username);
void increment_counters (char *username, long long cpu, long long read,
			 long long write, double tm);
GHashTable *get_counters_table ();
void add_tid_to_bad_list (pid_t pid);
long get_tid_size ();
void unlock_tid_data ();
void lock_tid_data ();

int get_cnt_threads (const char *username);
#ifdef TEST
void print_tid_data ();
#endif


#endif /* TID_TABLE_H_ */
