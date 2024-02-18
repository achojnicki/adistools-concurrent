from .constants import LEVEL_DEBUG, LEVEL_INFO, LEVEL_WARNING, LEVEL_FATAL, LEVEL_ERROR, LEVEL_SUCCESS

class adislog_methods:
    def debug(self, *args, **kwargs):
        self._message(LEVEL_DEBUG,*args, **kwargs)
    
    def info(self, *args, **kwargs):
        self._message(LEVEL_INFO,*args, **kwargs)
        
    def warning(self, *args, **kwargs):
        self._message(LEVEL_WARNING,*args, **kwargs)
    
    def error(self, *args, **kwargs):
        self._message(LEVEL_ERROR,*args, **kwargs)
    
    def fatal(self, *args, **kwargs):
        self._message(LEVEL_FATAL,*args, **kwargs)
    
    def success(self, *args, **kwargs):
        self._message(LEVEL_SUCCESS,*args, **kwargs)
         
