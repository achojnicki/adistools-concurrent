from workers_manager import Workers_manager
from tasks import Tasks
from daemon import Daemon
from pathlib import Path
from adisconfig import adisconfig

import sys
import adislog
import os

class adisconcurrent:
    _active=True
    _daemon=None
    _config=None
    _log=None

    _workers_manager=None
    _tasks=None
    
    def __init__(self):
        self._config=adisconfig('/etc/adisconcurrent/config.yaml')
        
        self._log=adislog.adislog(
            log_file=Path(self._config.log.logs_directory).joinpath("adisconcurrent_main_process.log"),
            replace_except_hook=False,
            debug=self._config.log.debug
            )
        
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