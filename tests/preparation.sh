#!/bin/bash

#-------------------------------------------------------------------
echo "mysqldd mysqldd 12000" > /etc/container/dbuser-map

echo "creating a new mysql user (mysqldd)..."
mysql --silent --host=localhost --user=root --execute "grant all privileges on *.* to mysqldd@localhost identified by 'newpasswd' with grant option;" > /dev/null 2>&1
sleep 5

echo "creating a new database..."
mysqladmin -umysqldd -pTTT create mybbdd; >/dev/null 2>&1
sleep 5

echo "creating a new table..."
mysql --silent --host=localhost --user=mysqldd --execute "use mybbdd; create table mybbddtab (id integer, name varchar(255)); insert mybbddtab (id, name) values(1234567890,'lkjhasdfhgddfqa'), (123456789,'dfjujdkhbasdfbnd'), (12345678,'kjghbnnbdfddsbfjhag'), (1234567,'ikjsvksjddfksdkjrbksjdhkj'), (123456,'kdfjasddnbkjqhkjhsd'), (12345,'iidnshfyrndfdd'), (1234,'jjfdhdyadfjsdnnhre'), (123,'sdflkjnndgdfhfdjjutyrndhkkd'), (12,'ndvhdjfkeldfshdyfjrjnf'), (1,'jfndfdhsydjrfkelsf');" > /dev/null 2>&1
sleep 5

#-------------------------------------------------------------------

echo "mytestsqld mytestsqld 11000" >> /etc/container/dbuser-map

echo "creating a new mysql user (mytestsqld)..."
mysql --silent --host=localhost --user=root --execute "grant all privileges on *.* to mytestsqld@localhost identified by 'newpasswd' with grant option;" >/dev/null 2>&1
sleep 5

echo "creating a new database..."
mysqladmin -umytestsqld -pTTT create mybdd; >/dev/null 2>&1
sleep 5

echo "creating a new table..."
mysql --silent --host=localhost --user=mytestsqld --execute "use mybdd; create table mybddtab (id integer, name varchar(255)); insert mybddtab (id, name) values(1234567890,'lkjhasdfhgdfqa'), (123456789,'dfjujkhbasdfbnd'), (12345678,'kjghbnnbdfdsbfjhag'), (1234567,'ikjsvksjddfkskjrbksjdhkj'), (123456,'kdfjasdnbkjqhkjhsd'), (12345,'iidnshfyrndfd'), (1234,'jjfhdyadfjsdnnhre'), (123,'sdflkjnngdfhfdjjutyrndhkkd'), (12,'nvhdjfkeldfshdyfjrjnf'), (1,'jfndfdhsydjrkelsf');" >/dev/null 2>&1

sleep 5

#-------------------------------------------------------------------

echo "mysqlslaptest mysqlslaptest 10000" >> /etc/container/dbuser-map

echo "creating a new mysql user (mysqlslaptest)..."
mysql --silent --host=localhost --user=root --execute "grant all privileges on *.* to mysqlslaptest@localhost identified by 'newpasswd' with grant option;"
sleep 5

echo "creating a new database..."
mysqladmin -umysqlslaptest -pTTT create pont;
sleep 5

echo "creating a new table..."
mysql --silent --host=localhost --user=mysqlslaptest --execute "use pont; create table ponttab (id integer, name varchar(255)); insert ponttab (id, name) values(1234567890,'lkjhasdfhgqa'), (123456789,'jujkhbasdfbnd'), (12345678,'kjghbnnbdsbfjhag'), (1234567,'ikjsvksjdkskjrbksjdhkj'), (123456,'kjasdnbkjqhkjhsd'), (12345,'iidnshfyrnd'), (1234,'jjfhdyajsdnnhre'), (123,'sdflkjnnghfdjjutyrndhkkd'), (12,'nvhdjfkelshdyfjrjnf'), (1,'jfndhsydjrkelsf');"
sleep 5

#-------------------------------------------------------------------