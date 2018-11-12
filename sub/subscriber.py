import asyncio
import asyncpg
import json
import os

import aio_pika
from uuid import uuid4
import logging

from asyncpg import DuplicateTableError, UniqueViolationError
from validate_email import validate_email


logger = logging.getLogger('simpleExample')
logger.setLevel(logging.INFO)


class Subscriber:
    """ Consumer from MQ to DB """

    def __init__(self):
        """ Subscriber constructor """
        self.rabbit_host = os.getenv('RABBIT_HOST', '127.0.0.1')
        self.rabbit_port = os.getenv('RABBIT_PORT', 5672)
        self.rabbit_user = os.getenv('RABBIT_USER', 'rabbitmq')
        self.rabbit_pass = os.getenv('RABBIT_PASS', 'rabbitmq')
        self.queue_name = os.getenv('QUEUE_NAME', 'contact')
        self.rabbit_url = f'amqp://{self.rabbit_user}:{self.rabbit_pass}@{self.rabbit_host}:{self.rabbit_port}/'
        self.db_host = os.getenv('DB_HOST', '127.0.0.1')
        self.db_port = os.getenv('DB_PORT', 5432)
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_pass = os.getenv('DB_PASS', 'pass')
        self.db_name = os.getenv('DB_NAME', 'contacts')
        self.db_url = f'postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}'
        self.connection = None
        self.channel = None
        self.queue = None
        self.db_conn = None

    async def db_setup(self):
        """ Async db setup"""
        self.db_conn = await asyncpg.connect(self.db_url)
        try:
            await self.db_conn.execute('''
                            CREATE TABLE contacts(
                                id varchar(36) PRIMARY KEY UNIQUE,
                                name text NOT NULL,
                                email text NOT NULL UNIQUE
                            )
                        ''')
        except DuplicateTableError:
            logger.info("Table already exists")

    async def init_setup(self):
        """ Async constructor setup"""
        self.connection = await aio_pika.connect_robust(self.rabbit_url, loop=loop)
        self.channel = await self.connection.channel()
        self.queue = await self.channel.declare_queue(self.queue_name, auto_delete=True)
        await self.db_setup()

    async def insert_contact(self, name, email):
        """
        Inserts entry to DB
        :param name: str
        :param email: str
        :return:
        """
        uuid = str(uuid4())
        try:
            await self.db_conn.execute('''
                    INSERT INTO contacts(id, name, email) VALUES($1, $2, $3)
                ''', uuid, name, email)
        except UniqueViolationError:
            logger.info("Email already exists")

    @staticmethod
    def msg_to_dict(data):
        return json.loads(data)

    async def consume(self):
        """ Coroutine for handling messages from MQ """
        await self.init_setup()
        async for message in self.queue:
            with message.process():
                msg = self.msg_to_dict(message.body)
                if validate_email(msg["email"]) and msg["name"]:
                    await self.insert_contact(**msg)


if __name__ == '__main__':
    subscriber = Subscriber()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(subscriber.consume())

