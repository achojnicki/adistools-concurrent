
import os
import sys
import signal
import pathlib


class DaemonizeException(Exception):
    pass
class PidFileException(DaemonizeException):
    pass

class Daemon:
    def __init__(
            self,
            root,
            pidfile,
            ):
        
        
        self._root=root
        self._log=self._root._log
                
        self._pidfile=pidfile

        self._stdin=sys.stdin
        self._stdout=sys.stdout
        self._stderr=sys.stderr
        
        self._null_stdin=open('/dev/null','r')
        self._null_stdout=open('/dev/null','a+')
        self._null_stderr=open('/dev/null','a+')
        
        
    def _prepare_pipes(self):
        self._stdout.flush()
        self._stderr.flush()
        
        os.dup2(self._stdin.fileno(),self._null_stdin.fileno())
        os.dup2(self._stdout.fileno(),self._null_stdout.fileno())
        os.dup2(self._stderr.fileno(),self._null_stderr.fileno())
 
    def _fork(self):
        try:
            pid=os.fork()
            if pid>0:
                sys.exit(0)
        except OSError:
            self._log.fatal('Failed to fork')
            
    def _write_pidfile(self):
        with open(self._pidfile,'w+') as pidfile:
            pidfile.write(str(os.getpid()))

    def _remove_pidfile(self):
        os.remove(self._pidfile)
        
    def _pid_exists(self, pid_file):
        return pathlib.Path(pid_file).is_file()
               
    def _set_env(self):
        os.setsid()
        os.umask(0)
        
    def stop(self):        
        self._root.stop()
        self._remove_pidfile()
    
    def _signal_handler(self, sig, frame):
        if sig==signal.SIGTERM:
            self.stop()
        
    def daemonize(self):
        
        self._fork()
        self._set_env()
        self._fork()
        self._write_pidfile()
        self._prepare_pipes()
    
        signal.signal(handler=self._signal_handler, signalnum=signal.SIGTERM)
        