from lib2to3 import fixer_base, refactor

import traceback

class scraper(fixer_base.BaseFix):
    PATTERN="simple_stmt"
    
    def __init__(self,line_number:int):
        super().__init__(None,None)
        
        self.lineno = line_number
        self.statement = ""
        
    def transform(self,n,r):
        if not self.statement and str(n).count('\n') > self.lineno - n.get_lineno():
            prev = str(n.prev_sibling)
            if prev == ' ':
                self.statement += prev.lstrip('\n')
                
            self.statement +=str(n)
        return n
    
class get_function_by_line(refactor.RefactoringTool):
    def __init__(self,s:str , l:int):
        self.source=s
        self.scraper=scraper(l)
        
        super().__init__(None)
    
    def get_fixers(self):
        return [[self.scraper], []]

    def __str__(self):
        self.refactor_string(self.source,'')
        return self.scraper.statement
    
def parse_frame(frame):
    resp={"code":str(get_function_by_line(open(frame.f_code.co_filename).read(),frame.f_lineno)),
          "locals":frame.f_locals,
          "globals":frame.f_globals,
          "line_number":frame.f_lineno,
          }
    return resp
    
