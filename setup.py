from adisscan import config
from adisscan import constants

import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host=config.rabbitmq.host,
        port=config.rabbitmq.port,
        credentials=pika.PlainCredentials(config.rabbitmq.user,config.rabbitmq.passwd)
        )
    )

channel=connection.channel()

try:
    print("Trying to create the awaiting ports queue: ", end="")
    channel.queue_declare(queue=constants.CONNECTION.AWAITING_PORTS_QUEUE)
    print("Success")

    print("Trying to create the scanned ports queue: ", end="")
    channel.queue_declare(queue=constants.CONNECTION.SCANNED_PORTS_QUEUE)
    print("Success")


except:
    print("Failed")
    raise