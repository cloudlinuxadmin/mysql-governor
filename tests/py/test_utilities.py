import mock
import pytest
import utilities
from pyfakefs import fake_filesystem


def test_exec_command_with_timeout_fail(monkeypatch):
    """
    When hit timeout, the RuntimeError is raised
    """
    monkeypatch.setattr('utilities.fDEBUG_FLAG', True)
    with pytest.raises(RuntimeError):
        utilities.exec_command_with_timeout('sleep 10', timeout=2)


def test_exec_command_with_timeout_success(monkeypatch, capfd):
    """
    When command executed successfully, the output goes to standard stream
    Also testing consuming of generated commands
    """
    msg = 'Hello, world!'
    monkeypatch.setattr('utilities.fDEBUG_FLAG', True)
    utilities.exec_command_with_timeout('echo %s' % msg)
    out, err = capfd.readouterr()
    assert msg in out


conf1 = """
[client-server]
!includedir /etc/my.cnf.d
"""
conf2 = """
[mysqld]
pid-file=/var/run/mysqld/mysqld.pid
default-storage-engine=MyISAM
innodb_file_per_table=1
"""
conf3 = """
[mysqld]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
default-storage-engine=MyISAM
"""
conf4 = """
[mysqld]
performance-schema=0
datadir=/var/lib/mysql
performance-schema=0
log-error=/var/log/mysqld.log
"""


@pytest.mark.parametrize("mocked_content, expected", [
    (conf1, ''),
    (conf2, ''),
    (conf3, '/var/log/mysqld.log'),
    (conf4, '/var/log/mysqld.log')
], ids=['no_section', 'no_option', 'str_option', 'duplicated_options'])
def test_get_mysql_cnf_value(mocked_content, expected, option='log-error'):
    """
    Read log-error option from given example of /etc/my.cnf
    """
    with mock.patch('builtins.open', mock.mock_open(read_data=mocked_content)):
        assert utilities.get_mysql_cnf_value('mysqld', option) == expected


@pytest.mark.parametrize("mocked_content", [conf1, conf4], ids=['simple_options', 'duplicated_options'])
def test_read_config(mocked_content):
    """
    Test reading config files
    """
    with mock.patch('builtins.open', mock.mock_open(read_data=mocked_content)):
        assert utilities.read_config_file('')


def test_mycnf_absent(fs):
    """
    Check the 'mycnf_writable' function in case of my.cnf file is absent
    """
    fs.add_mount_point('/etc')
    assert utilities.mycnf_writable()


def test_mycnf_writable(fs):
    """
    Check the 'mycnf_writable' function in case of my.cnf is writable.
    """
    fs.create_file('/etc/my.cnf')
    assert utilities.mycnf_writable()


def test_mycnf_read_only(fs):
    """
    Check the 'mycnf_writable' function in case of my.cnf is not writable.
    """
    fs.create_file('/etc/my.cnf')
    fake_filesystem.set_uid(1)
    os_module = fake_filesystem.FakeOsModule(fs)
    os_module.chmod('/etc/my.cnf', 0o400)
    assert not utilities.mycnf_writable()
