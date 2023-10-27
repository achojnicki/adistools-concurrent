#!/usr/bin/env python3

from workers_manager import Workers_manager
from uwsgi_manager import Uwsgi_manager
from tasks import Tasks
from daemon import Daemon

from adislog import adislog
from pathlib import Path
from adisconfig import adisconfig
from sys import exit
from signal import signal, SIGTERM

class adisconcurrent:
    _active=None

    _daemon=None
    _config=None
    _log=None
    _workers_manager=None
    _uwsgi_manager=None
    _tasks=None
    
    def __init__(self):
        #initialisation of the config module
        self._config=adisconfig('/opt/adistools/configs/adistools-concurrent.yaml')

        #initialisation of the log module
        self._log=adislog(
            app_name="adistools-concurrent",
            backends=['file_plain' if self._config.general.daemonize else 'terminal_table'],
            log_file=Path(self._config.directories.logs_directory).joinpath("adistools-concurrent.log"),
            replace_except_hook=False,
            debug=self._config.log.debug,
            privacy=True if self._config.log.debug else False,
            )
        
        self._log.info("Initialising Adi's Concurrent")

        #binding for the signals
        signal(handler=self._signal_handler, signalnum=SIGTERM)

        #initialisation of the daemonization module
        if self._config.general.daemonize:
            self._daemon=Daemon(
                root=self,
                pidfile=self._config.daemon.pid_file
                )
        
        #initialisating all of the child objects
        self._tasks=Tasks(self)
        self._workers_manager=Workers_manager(self)
        self._uwsgi_manager=Uwsgi_manager(self)
        
        #starting workers if enabled in config
        if self._config.general.start_workers:
            self._workers_manager.scan_for_workers()
            self._tasks.add_task('workers_manager',self._workers_manager.task, 100)
        
        #starting UWSGI workers if enabled in config
        if self._config.general.start_uwsgi_workers:
            self._uwsgi_manager.scan_for_uwsgi_ini_files()
            self._tasks.add_task('uwsgi_manager',self._uwsgi_manager.task, 100)

        self._log.success("Initialisation of adistools-concurrent successed")

    def _signal_handler(self, sig, frame):
        """Callback handler for the signal coming from OS"""
        self._log.debug('Got the signal')
        if sig==SIGTERM:
            self.stop()

    def stop(self):
        self._log.info('Got the termination signal. Starting procedure...')

        self._active=False
        self._tasks.stop()
        self._workers_manager.stop()
        self._uwsgi_manager.stop()
        if self._daemon:
            self._daemon.stop()
        self._log.success('Exitting...')
        exit(0)
        

    def start(self):
        self._log.debug("Called start method")
        self._active=True
        if self._daemon:
            self._log.info('Starting as daemon...')
            self._daemon.daemonize()
            
        self._tasks.start()

if __name__=="__main__":
    ac=adisconcurrent()
    ac.start()