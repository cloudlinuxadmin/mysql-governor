mysql --silent --host=localhost --user=mysqldd --execute "use mybbdd; select count(*) from mybbddtab as t1, mybbddtab as t2, mybbddtab as t3, mybbddtab as t4, mybbddtab as t5, mybbddtab as t6, mybbddtab as t7, mybbddtab as t8, mybbddtab as t9 where t1.name like '%a%';" > /dev/null 2>&1

sleep 5

mysql --silent --host=localhost --user=mytestsqld --execute "use mybdd; select count(*) from mybddtab as t1, mybddtab as t2, mybddtab as t3, mybddtab as t4, mybddtab as t5, mybddtab as t6, mybddtab as t7, mybddtab as t8, mybddtab as t9 where t1.name like '%a%';"

sleep 5

mysql --silent --host=localhost --user=mysqlslaptest --execute "use pont; select count(*) from ponttab as t1, ponttab as t2, ponttab as t3, ponttab as t4, ponttab as t5, ponttab as t6, ponttab as t7, ponttab as t8, ponttab as t9 where t1.name like '%a%';"