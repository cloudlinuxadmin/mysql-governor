/*
 * calc_stats.h
 *
 *  Created on: Aug 7, 2012
 *      Author: alexey
 */

#ifndef CALC_STATS_H_
#define CALC_STATS_H_

#include "data.h"
#include "tid_table.h"

#include "stats.h"

void clac_stats_difference(client_data * new, tid_table * old, Stats * st);
void clac_stats_difference_inner(long long cpu, long long read, long long write, tid_table * old, Stats * st);
void proceed_accounts(double tm);
Stats *add_new_stats(username_t username, Stats * st, long long tick_id);
void add_empty_stats_for_uid(username_t username);
void free_accounts_and_users();
void init_accounts_and_users();
void print_to_restrict_log_stats(void *data);
void lock_acc();
void unlock_acc();
void *get_accounts();

void clac_stats_difference_inner_from_counter(long long cpu, long long read, long long write, double tm_in, Stats * st, double new_tm);
void clac_stats_difference_add_to_counters(client_data * new, tid_table * old);
void clac_stats_difference_inner_add_to_counters(long long cpu, long long read, long long write, tid_table * old);
int is_user_ignored(char *user_name);

//--- for dbctl ---------------------------------------------------------------
void dbctl_restrict_set(gpointer key, Account * ac, void *data);
void dbctl_unrestrict_set(gpointer key, Account * ac, void *data);
void dbctl_unrestrict_all_set(gpointer key, Account * ac, void *data);
void reinit_users_list();

#endif /* CALC_STATS_H_ */
