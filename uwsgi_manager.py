from pathlib import Path
from subprocess import Popen, PIPE
from os import environ, getcwd, listdir, chdir, kill, setuid, setgid
from copy import deepcopy
from select import select

def demote(uid, gid):
    def change_uid_gid():
        setgid(gid)
        setuid(uid)
    return change_uid_gid


class Uwsgi_manager:
    _root=None
    _log=None
    _config=None

    _workers={}
    _active_workers=[]

    def __init__(self, root):
        self._root=root
        self._log=root._log
        self._log.info('Starting initialization of the Uwsgi_manager')
        self._config=root._config        
        self._log.success('Initialisation of successed!')


    def _count_active_workers(self, name:str):
        count=0
        for a in self._active_workers:
            if a['name']==name:
                count+=1
        return count

    def _start_workers(self,name):        
        for _ in range(self._count_active_workers(name),1):
            self._start_worker(name)
            
    def _start_worker(self,name):
        self._log.info('Starting UWSGI worker: '+name)
        worker=self._workers[name]

        p=Popen(
                [
                    worker['exec'].absolute(),
                    '--ini',
                    worker['ini_file']
                ],
                shell=False,
                preexec_fn=demote(worker['uid'],worker['gid']),
                stdout=PIPE,
                stderr=PIPE
                )

        self._active_workers.append({
            "name":name,
            'process_obj': p
        })
        
    def _clear_zombies(self):
        for worker in self._active_workers:
            if worker['process_obj'].poll() != None:
                del self._active_workers[self._active_workers.index(worker)]

    def _declare_uwsgi_worker(self,name:str, exec:Path, ini_file:Path, uid:int, gid:int, **kwargs): 
        self._workers[name]={
            "name":name,
            "exec":exec,
            "ini_file":ini_file,
            "uid":uid,
            "gid":gid
             }

    def scan_for_uwsgi_ini_files(self):
        path=Path(self._config.uwsgi.ini_directory)
        for file_name in listdir(path):
            ini_file=deepcopy(path).joinpath(file_name)
            if ini_file.is_file():
                self._declare_uwsgi_worker(
                    name=file_name,
                    exec=Path(self._config.uwsgi.uwsgi_executable_path),
                    ini_file=ini_file,
                    uid=self._config.uwsgi.uid,
                    gid=self._config.uwsgi.gid
                )
                
                        
    def _stop_workers(self):
        for worker in self._active_workers:
            process=worker['process_obj']
            kill(process.pid, 15)
    
    def stop(self):
        self._stop_workers()

    def task(self):
        # check for zombie processes
        self._clear_zombies()

        #start workers
        for worker in self._workers:
            self._start_workers(worker)
        
        #iterate through all active UWSGI workers and get the data from STDIN, STDERR
        for process in self._active_workers:
            x=[process['process_obj'].stdout,process['process_obj'].stderr]
            r, w, e=select(x,[],[], .000001)
            for a in r:
                data=a.readline().decode('utf-8')
                self._log.info(
                    'Message from the {name}\'s: {data}'.format(name=process['name'], data=data)
                )
            
