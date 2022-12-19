#!/usr/bin/python3

from workers_manager import Workers_manager
from uwsgi_manager import Uwsgi_manager

from tasks import Tasks
from daemon import Daemon
from adislog import adislog

from pathlib import Path
from adisconfig import adisconfig
from sys import exit


class adisconcurrent:
    _active=None

    _daemon=None
    _config=None
    _log=None
    _workers_manager=None
    _tasks=None
    
    def __init__(self):
        #initialisation of the config module
        self._config=adisconfig('/etc/adisconcurrent/config.yaml')

        #initialisation of the log module
        backends=['file_plain' if self._config.general.daemonize else 'terminal_table']
        self._log=adislog(
            backends=backends,
            log_file=Path(self._config.log.logs_directory).joinpath("adisconcurrent_main_process.log"),
            replace_except_hook=False,
            debug=self._config.log.debug,
            privacy=True if self._config.log.debug else False,
            )
        
        self._log.info("Initialising Adi's Concurrent")
        
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
        
        #scanning for the workers
        self._workers_manager.scan_for_workers()
        self._uwsgi_manager.scan_for_uwsgi_ini_files()

        #adding workers manager task to the event loop of main process
        self._tasks.add_task('workers_manager',self._workers_manager.task, 100)
        self._tasks.add_task('uwsgi_manager',self._uwsgi_manager.task, 100)

        self._log.success("Initialisation of adisconcurrent successed")

        
    def stop(self):
        self._log.info('Got the stop signal. starting the stop procedure...')
        
        self._active=False

        self._tasks.stop()
        self._workers_manager.stop()
        self._uwsgi_manager.stop()
        
        self._log.info('Exitting...')
        
        exit(0)
        

    def start(self):
        self._log.info("Called starting procedure")

        self._active=True

        if self._daemon:
            self._log.info('starting as daemon')
            self._daemon.daemonize()
            
        self._tasks.start()

if __name__=="__main__":
    ac=adisconcurrent()
    ac.start()