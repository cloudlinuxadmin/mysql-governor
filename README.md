mysql-governor
==============

MySQL governor is set of utilities to monitor and throttle MariaDB & MySQL usage on per user bases. It is especially useful in shared hosting environemnt. The monitoring is done via resource usage statistics per each MySQL thread.
The governor can monitor and display in real time CPU and IO (reads & writes) usage.

For throttling CloudLinux LVE technology is used. Throttling is currently impossible on other platforms.

When used in conjunction with CloudLinux kernel & LVE, MySQL Governor allows to throttle customers who use too much resources. It supports following limits:
CPU         %     CPU speed relative to one core. 150% would mean one and a half cores
READ        bytes bytes read. Cached reads are not counted, only those that were actually read from disk will be counted
WRITE       bytes bytes written. Cached writes are not counted, only once data is written to disk, it is counted

You can set different limits for different periods: current, short, med, long. By default those periods are defined as 1 second, 5 seconds, 1 minute and 5 minutes. They can be re-defined using configuration file. The idea is to use larger acceptable values for shorter periods. Like you could allow a customer to use two cores (200%) for one second, but only 1 core (on average) for 1 minute, and only 70% within 5 minutes. That would make sure that customer can burst for short periods of time.
 
When customer is restricted, the customer will be placed into special LVE with ID 3. All restricted customers will be placed into that LVE, and you can control amount of resources available to restricted customers. Restricted customers will also be limited to only 30 concurrent connections. This is done so they wouldn't use up all the MySQL connections to the server.
