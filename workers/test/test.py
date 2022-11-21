from adisscan import config, constants
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from json import loads
import adislog
import socket

class port_worker:
    _config=config
    _log=adislog.adislog(
        log_file="logs\port_worker.log",
        replace_except_hook=False,
    )
    _rabbitmq_conn=None
    def __init__(self):
        self._init_rabbitmq()

    def _init_rabbitmq(self):
        self._rabbitmq_conn=BlockingConnection(
            ConnectionParameters(
                host=self._config.rabbitmq.host,
                port=self._config.rabbitmq.port,
                credentials=PlainCredentials(
                    self._config.rabbitmq.user,
                    self._config.rabbitmq.passwd
                )))
        self._rabbitmq_channel=self._rabbitmq_conn.channel()

    def _test_host(self,host,port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            try:
                s.connect((host,port))
                result=True
            except:
                result=False
        return result

    def _callback(self, channel,  method, properties, body):
        body=body.decode('utf-8')
        data=loads(body)

        test_result=self._test_host(**data['test_data'])

        if test_result:
            self._log.success("Service active at {0}:{1} ".format(data['test_data']['host'], data['test_data']['port']))
        else:
            self._log.fatal("Service at {0}:{1} unreachable".format(data['test_data']['host'], data['test_data']['port']))

    def start(self):
        self._log.info('Starting port_worker')

        self._rabbitmq_channel.basic_consume(queue=constants.CONNECTION.AWAITING_PORTS_QUEUE,
                                             auto_ack=True,
                                             on_message_callback=self._callback
                              )
        self._rabbitmq_channel.start_consuming()


if __name__=="__main__":
    port_worker=port_worker()
    port_worker.start()
