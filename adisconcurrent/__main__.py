from workers_manager import Workers_manager
from tasks import Tasks

from sys import argv
from pathlib import Path

import config

import adislog


class adisconcurrent:
    _active=True

    _config=config
    _log=adislog.adislog(
        log_file="logs\log.log",
        replace_except_hook=False,
        debug=True if 'debug' in argv else False
    )

    _workers_manager=None
    _tasks=None

    def __init__(self):
        self._log.info("Initialising Adi's Concurrent")

        #initialisating all of the child objects
        self._workers_manager=Workers_manager(self)
        self._tasks=Tasks(self)

        #declaring active workers
#        self._workers_manager.declare(name='port_worker',
#                                      exec=Path("C:\\Users\\arjel\\AppData\\Local\\Programs\\Python\\Python310\\python.exe"),
#                                      script=Path(".\\adisscan\scanner\port_worker.py"),
#                                      workers=1)

        self._workers_manager._scan_for_modules()

        #declaring active tasks of main process
        self._tasks.add_task('workers_manager',self._workers_manager.task, 100)

        self._log.success("Initialisation of Adi's Scan finished")

    def start(self):
        self._log.info("Called starting procedure")
        self._tasks.start()

if __name__=="__main__":
    acn=adisconcurrent()
    acn.start()