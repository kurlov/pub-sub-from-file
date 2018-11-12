import asyncio
import json
import os

import aio_pika
import aiofiles
from validate_email import validate_email


class Publisher:
    """ Publisher from file to MQ """

    def __init__(self):
        """
        Publisher constructor, most parameters parsed via ENVs.
        """
        self.rabbit_host = os.getenv('RABBIT_HOST', '127.0.0.1')
        self.rabbit_port = os.getenv('RABBIT_PORT', 5672)
        self.rabbit_user = os.getenv('RABBIT_USER', 'rabbitmq')
        self.rabbit_pass = os.getenv('RABBIT_PASS', 'rabbitmq')
        self.routing_key = os.getenv('ROUTING_KEY', 'contact')
        self.rabbit_url = f"amqp://{self.rabbit_user}:{self.rabbit_pass}@{self.rabbit_host}:{self.rabbit_port}/"
        self.connection = None
        self.channel = None

    @staticmethod
    def msg_to_bytes(data):
        return json.dumps(data)

    @staticmethod
    def clean_entries(entries):
        """ Remove white space characters from strings"""
        return list(map(lambda x: x.strip(), entries))

    async def init_setup(self):
        """ Async constructor for I/O related handlers"""
        self.connection = await aio_pika.connect_robust(self.rabbit_url, loop=loop)
        self.channel = await self.connection.channel()

    async def shutdown(self):
        """ Async cleaner for I/O related handlers"""
        await self.connection.close()

    async def send_msg(self, msg_data):
        msg = self.msg_to_bytes(msg_data)
        if not self.channel:
            await asyncio.sleep(1)
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=msg.encode()
            ),
            routing_key=self.routing_key
        )

    @staticmethod
    def parse_line(line):
        """
        Checks line from file to be valid for passing as name with email address
        :param line: str
        :return: bool, dict
        """
        entries = line.split(",")
        entries = Publisher.clean_entries(entries)
        if len(entries) == 2:
            name = entries[0]
            email = entries[1]
            if validate_email(email) and name:
                data = dict(name=name, email=email)
                return True, data
        return False, {}

    async def read_file(self, file_name):
        """
        Reads input file line by line
        :param file_name: str
        :return: awaitable
        """
        await self.init_setup()
        async with aiofiles.open(file_name, mode='r') as f:
            async for line in f:
                is_valid, data = self.parse_line(line)
                if is_valid:
                    await self.send_msg(data)
        await self.shutdown()


if __name__ == '__main__':
    publisher = Publisher()
    filename = os.getenv('FILENAME', 'data.csv')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(publisher.read_file(filename))

