import mock
import dbgovernor_map
import dbgovernor_map_plesk


def test_mysqldb_error_da(capsys, monkeypatch):
    class MonkeyPatch():
        def readlines(self):
            return ['user=user','passwd=passwd']
        def close(self):
            return
    monkeypatch.setattr('__builtin__.open', lambda x: MonkeyPatch())
    with mock.patch('dbgovernor_map.get_dauser', return_value=dict()):
        dbgovernor_map.get_account_list()
        out, err = capsys.readouterr()
        assert "Can't connect" in out


def test_mysqldb_error_plesk(capsys):
    with mock.patch('dbgovernor_map_plesk.read_mysql_conn_params', return_value={'login': '', 'pass': ''}):
        dbgovernor_map_plesk.get_users_data()
        out, err = capsys.readouterr()
        assert "Can't connect" in out
