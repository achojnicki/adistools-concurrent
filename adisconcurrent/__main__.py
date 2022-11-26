from workers_manager import Workers_manager
from tasks import Tasks
from daemon import Daemon
from pathlib import Path

import config
import sys
import adislog
import os

class adisconcurrent:
    _active=True
    _daemon=None
    _config=config
    _log=adislog.adislog(
        log_file="logs/log.log",
        replace_except_hook=False,
        debug=True if 'debug' in sys.argv else False
    )

    _workers_manager=None
    _tasks=None
    
    def _prepare_pipes_bindings(self):
        null_stdin=open('/dev/null','r')
        null_stdout=open('/dev/null','a+')
        null_stderr=open('/dev/null','a+')
        
        os.dup2(sys.stdin.fileno(),null_stdin.fileno())
        os.dup2(sys.stdout.fileno(),null_stdout.fileno())
        os.dup2(sys.stderr.fileno(),null_stderr.fileno())
        
        sys.stdin=None
        sys.stdout=None
        sys.stderr=None
        
    def __init__(self):
        self._log.info("Initialising Adi's Concurrent")
        
        if self._config.general.daemonize:
            self._daemon=Daemon(
                root=self,
                pidfile=self._config.daemon.pid_file
                )
        #initialisating all of the child objects
        self._workers_manager=Workers_manager(self)
        self._tasks=Tasks(self)

        self._workers_manager.scan_for_modules()
        self._tasks.add_task('workers_manager',self._workers_manager.task, 100)

        self._log.success("Initialisation of adisconcurrent finished")

    def stop(self):
        self._log.info('Got the exit signal. starting the stop procedure...')
        
        self._active=False
        self._workers_manager.stop_workers()
        
        sys.exit(0)
        

    def start(self):
        
        self._log.info("Called starting procedure")
        if self._daemon:
            self._log.info('starting as daemon')
            self._daemon.daemonize()
            
        self._tasks.start()

if __name__=="__main__":
    acn=adisconcurrent()
    acn.start()