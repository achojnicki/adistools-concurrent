from constants.tasks import TIME_DIVIDER

from time import sleep,time


import os
import sys

class Tasks:
    _root=None

    #[name,callback,execution_delay(ms),previous_execution_time]
    _tasks=[]
    def __init__(self,root):
        self._root=root
        self._log=root._log
        self._config=root._config

        self._time_divider=TIME_DIVIDER


    def add_task(self,name,callback,execution_interval=None):
        self._tasks.append([name,callback,execution_interval,0])

    def loop(self):
        try:
            time_divider=self._time_divider
            while self._root._active:
                for a in self._tasks:
                    self._log.debug('Calling task: '+a[0])
                    #execution interval doesnt matter
                    if not a[2]:
                        a[1]()
                        self._log.debug('Task ')
    
    
                    #execution interval matter
                    else:
                        #exec time milis
                        t=time()*time_divider
    
                        if t-a[3]>=a[2]:
                            a[1]()
                            a[3]=time()*time_divider
                    self._log.debug('finished. time of execution: '+str(a[3]))
                sleep(self._config.tasks.delay)
        except KeyboardInterrupt:
            self._root.stop()
    def start(self):
        self._log.info('Starting tasks module...')
        self.loop()
    def stop(self):
        self.active=False