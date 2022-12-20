from constants.workers_manager import MANIFEST_FILE
from pathlib import Path
from subprocess import Popen
from os import environ, getcwd, listdir, chdir, kill, setuid, setgid
from yaml import safe_load
from copy import deepcopy

def demote(uid, gid):
    def change_uid_gid():
        setgid(gid)
        setuid(uid)
    return change_uid_gid

class Workers_manager:
    _root=None
    _log=None
    _config=None

    _workers={}
    _active_workers=[]

    def __init__(self, root):
        self._root=root
        self._log=root._log
        self._log.info('Starting initialization of the Workers_manager')
        
        self._config=root._config
        
        self._log.success('Initialisation of workers_manager successed!')

    def _count_active_workers(self, name:str):
        count=0
        for a in self._active_workers:
            if a['name']==name:
                count+=1
        return count

    def _start_workers(self,name):        
        for _ in range(self._count_active_workers(name),self._workers[name]['workers']):
            self._start_worker(name)
                    
    def _generate_python_path(self, worker_dir):
        return "{0}:{1}".format(getcwd(), worker_dir)
    
    def _start_worker(self,name):
        self._log.info('Starting worker: '+name)
        worker=self._workers[name]

        env=environ.copy()
        env['PYTHONPATH']=self._generate_python_path(worker['worker_dir'])
        
        chdir(worker['worker_dir'])
        p=Popen(
                [
                    worker['exec'].absolute(),
                    worker['script'].absolute()
                ],
                env=env,
                shell=False,
                preexec_fn=demote(worker['uid'], worker['gid'])
                )

        self._active_workers.append({
            "name":name,
            'process_obj': p
        })
        
    def _clear_zombies(self):
        self._log.debug('Cleaning zombie processes')
        for worker in self._active_workers:
            if worker['process_obj'].poll() != None:
                del self._active_workers[self._active_workers.index(worker)]
        self._log.debug('Zombies cleaned')

    def _declare_worker(self,name:str, exec:Path, script:Path, workers:int, worker_dir:Path, uid:int, gid: int, **kwargs):
        self._workers[name]={
            "name":name,
            "exec":exec,
            "script":script,
            "workers":workers,
            "worker_dir":worker_dir,
            "uid":uid,
            "gid":gid
             }

    def _parse_manifest(self, manifest_path:Path):
        with open(manifest_path, 'r') as manifest_file:
            return safe_load(manifest_file)
            

    def scan_for_workers(self):
        path=Path(self._config.general.workers_directory)
        for worker_dir in listdir(path):
            worker_directory=deepcopy(path).joinpath(worker_dir)
            if worker_directory.is_dir():
                #TODO: add exceptions
                worker_maifest_path=worker_directory.joinpath(MANIFEST_FILE)
                if worker_maifest_path.is_file():
                    args=self._parse_manifest(worker_maifest_path)
                    if args['enabled'] == True:
                        args['exec']=Path(args['exec'])
                        args['script']=worker_directory.joinpath(args['script'])
                        args['worker_dir']=worker_directory
                        self._declare_worker(**args)
                        
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
