from constants.tasks import TIME_DIVIDER

from time import sleep,time


import os
import sys

class Tasks:
    _active=None
    _root=None

    #[name,callback,execution_delay(ms),previous_execution_time]
    _tasks=[]
    def __init__(self,root):
        self._root=root
        self._log=root._log

        self._log.info("initializating Tasks module...")
        self._config=root._config

        self._time_divider=TIME_DIVIDER

        self._log.success('initialization of the tasks module successed.')


    def add_task(self,name,callback,execution_interval=None):
        self._tasks.append([name,callback,execution_interval,0])

    def _loop(self):
        self._log.info("Starting Task's mainloop")
        try:
            time_divider=self._time_divider
            while self._active:
                for a in self._tasks:
                    #execution interval doesn't matter
                    if not a[2]:
                        a[1]()
    
                    #execution interval matter
                    else:
                        #exec time milis
                        t=time()*time_divider
    
                        if t-a[3]>=a[2]:
                            a[1]()
                            a[3]=time()*time_divider
                sleep(self._config.tasks.interval)
        except KeyboardInterrupt:
            self._root.stop()

    def start(self):
        self._log.info('Starting tasks module...')
        
        self._active=True
        self._loop()


    def stop(self):
        self._log.info("Stopping Tasks module...")
        
        self._active=False

        self._log.info('Tasks module stopped')