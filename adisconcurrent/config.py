class startup:
    daemonize=True
    
class daemon:
    pid_file='adisconcurrent.pid'
    
class rabbitmq:
    host="127.0.0.1"
    port=5672
    vhost='/'

    user='adrian'
    passwd='gwh28'

class mongo:
    db_url="mongodb://localhost:27017"
    db='adisscan'

    user=None
    passwd=None

class tasks:
    delay=0.1