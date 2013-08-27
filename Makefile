VERSION=1.0
PWD=$(shell pwd)
sources:
	ln -s $(PWD)/../mysql-governor $(PWD)/../governor-mysql-$(VERSION)
	cd $(PWD)/../governor-mysql-$(VERSION)
	/bin/tar cfz ./governor-mysql-$(VERSION).tar.bz2 $(PWD)/../governor-mysql-$(VERSION)/cmake/ $(PWD)/../governor-mysql-$(VERSION)/cron/ $(PWD)/../governor-mysql-$(VERSION)/install/ $(PWD)/../governor-mysql-$(VERSION)/mysql/ $(PWD)/../governor-mysql-$(VERSION)/script/ $(PWD)/../governor-mysql-$(VERSION)/src/ $(PWD)/../governor-mysql-$(VERSION)/tests/ $(PWD)/../governor-mysql-$(VERSION)/CMakeLists.txt $(PWD)/../governor-mysql-$(VERSION)/db-governor.xml $(PWD)/../governor-mysql-$(VERSION)/db-governor.xml.example $(PWD)/../governor-mysql-$(VERSION)/db-governor.xml.test $(PWD)/../governor-mysql-$(VERSION)/db_governor.spec $(PWD)/../governor-mysql-$(VERSION)/LICENSE.TXT
	rm -f $(PWD)/../governor-mysql-$(VERSION)
