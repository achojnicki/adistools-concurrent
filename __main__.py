#!/usr/bin/env python3

from workers_manager import Workers_manager
from uwsgi_manager import Uwsgi_manager
from scheduler import Scheduler
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
    _scheduler=None
    
    def __init__(self):
        #initialisation of the config module
        self._config=adisconfig('/opt/adistools/configs/adistools-concurrent.yaml')

        self._config_workers=adisconfig('/opt/adistools/configs/adistools-concurrent_workers.yaml')
        self._config_uwsgi_workers=adisconfig('/opt/adistools/configs/adistools-concurrent_uwsgi_workers.yaml')

        _backends=[]
        if not self._config.general.daemonize:
            if self._config.log.print_log:
                if self._config.log.print_log_mode == 'colorful':
                    _backends.append('terminal_colorful')
                elif self._config.log.print_log_mode == 'table':
                    _backends.append('terminal_table')
                elif self._config.log.print_log_mode == 'terminal':
                    _backends.append('terminal')
        else:
            if self._config.log.report_to_systemd:
                _backends.append('terminal')

        if self._config.log.save_to_file:
            _backends.append('file_plain')


        #initialisation of the log module
        self._log=adislog(
            project_name="adistools-concurrent",
            backends=_backends,
            log_file=Path(self._config.directories.logs_directory).joinpath("adistools-concurrent.log"),
            debug=self._config.log.debug,
            privacy=self._config.log.privacy,
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
        self._scheduler=Scheduler(self)
        self._workers_manager=Workers_manager(self)
        self._uwsgi_manager=Uwsgi_manager(self)
        
        #starting workers if enabled in config
        if self._config.general.start_workers:
            self._workers_manager.load_workers()
            self._scheduler.add_task('workers_manager',self._workers_manager.task, 100)
        
        #starting UWSGI workers if enabled in config
        if self._config.general.start_uwsgi_workers:
            self._uwsgi_manager.load_uwsgi_workers()
            self._scheduler.add_task('uwsgi_manager',self._uwsgi_manager.task, 100)

        self._log.info("Initialisation of adistools-concurrent succeeded")

    def _signal_handler(self, sig, frame):
        """Callback handler for the signal coming from OS"""
        self._log.debug('Got the signal')
        if sig==SIGTERM:
            self.stop()

    def stop(self):
        self._log.debug('Got termination signal. Starting procedure...')

        self._active=False
        self._scheduler.stop()
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
            
        self._scheduler.start()

if __name__=="__main__":
    ac=adisconcurrent()
    ac.start()