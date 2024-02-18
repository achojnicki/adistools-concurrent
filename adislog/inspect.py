from inspect import stack

class inspect:
    def __init__(self, privacy:bool):
        self._privacy=privacy
    
    def _clean(self,data):
        data=bytearray(data, 'utf-8')
        while 1:
            if data[0] == ord(' ') or data[0] == ord('\t') or data[0]==ord("\n"):
                del data[0]
            else:
                break
        if data[-1] == ord("\n"):
            del data[-1]
            
        data=data.decode('utf-8')
        data.replace('\n','<newline>')
        return data
        
    def get_caller(self):
        i=stack()[3]
        resp={"filename":i.filename,
              "function": i.function if self._privacy else self._clean(i.code_context[0]),
              "line_number":i.lineno}
        return resp
