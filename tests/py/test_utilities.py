import pytest
import utilities


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
