from adislog import adislog
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from json import loads
from pymongo import MongoClient

import config
import requests
import signal


class pixel_tracker_processor:
    def __init__(self):
        self._busy=False
        
        self._config=config
        
        
        self._log=adislog(
            backends=['file_plain'],
            debug=True,
            replace_except_hook=False,
            log_file='logs/log.log'
            )
        
        self._mongo_conn=MongoClient(
            self._config.mongo.host,
            self._config.mongo.port
            )
        
        self._mongo_db=self._mongo_conn[self._config.mongo.db]
        self._pixel_trackers=self._mongo_db['pixel_trackers']
        self._pixel_trackers_metrics=self._mongo_db['pixel_trackers_metrics']
        
        self._rabbitmq_conn=BlockingConnection(
            ConnectionParameters(
                host=self._config.rabbitmq.host,
                port=self._config.rabbitmq.port,
                credentials=PlainCredentials(
                    self._config.rabbitmq.user,
                    self._config.rabbitmq.passwd
                    )
                )
            )
        self._rabbitmq_channel=self._rabbitmq_conn.channel()
        self._rabbitmq_channel.basic_consume(
            'pixel_tracking_incoming',
            self._incoming_data_callback
            )
    
    def _get_addr_details(self, addr):
        try:
            r=requests.get('http://ip-api.com/json/{addr}'.format(addr=addr))
        
            d=r.json()
            self._log.success('Obtained host details.')
            return d if d['status'] == 'success' else None
        except:
            self._log.error('Obtaining host details failed.')
            return None

    def _tracker_exists(self, tracker_uuid):
        query={
            "tracker_uuid":tracker_uuid
            }
        return True if self._pixel_trackers.find_one(query) is not None else False
    def _get_tracker_owner(self, tracker_uuid):
        query={"tracker_uuid":tracker_uuid}
        return self._pixel_trackers.find_one(query)['user_uuid']
        
    
    def _incoming_data_callback(self, channel, method_frame, header_frame, data):
        self._busy=True
        
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        
        data=loads(data.decode('utf-8'))
        
        tracker_uuid=data['tracker_uuid']
        if tracker_uuid:
            if self._tracker_exists(tracker_uuid):
                request_details=data['request_details']
                addr=data['request_details']['REMOTE_ADDR']
                host_details=self._get_addr_details(addr)
                user_uuid=self._get_tracker_owner(tracker_uuid)
                timestamp=data['timestamp']

                
                
                document={
                    "tracker_uuid"     : tracker_uuid,
                    "request_details"  : request_details,
                    "user_uuid"        : user_uuid,
                    "host_details"     : host_details,
                    "timestamp"        : timestamp,
                    
                    }
                self._pixel_trackers_metrics.insert_one(document)
                
                self._log.success('Incoming data processed successfully.')

            else:
                self._log.warning("tracker-uuid({tracker_uuid}) doesn't exists".format(tracker_uuid=tracker_uuid))
        else:
            self._log.warning("tracker_uuid isn't provided")
        self._busy=False
        
    
    def start(self):
        try:
            self._rabbitmq_channel.start_consuming()
        except:
            self._rabbitmq_channel.stop_consuming()
            raise
    
if __name__=="__main__":
    ptip=pixel_tracker_processor()
    ptip.start()