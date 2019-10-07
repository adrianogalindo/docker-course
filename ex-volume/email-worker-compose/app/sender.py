import psycopg2
import redis
import json
import os
from bottle import Bottle, request


class Sender(Bottle):
    def __init__(self):
        super().__init__()
        self.route('/', method='POST', callback=self.send)
        
        redis_host = os.getenv('REDIS_HOST', 'queue')
        self.queuenetwork = redis.StrictRedis(host=redis_host, port=6379, db=0)

        db_host = os.getenv('DB_HOST', 'db')
        db_user = os.getenv('DB_USER', 'postgres')
        db_name = os.getenv('DB_NAME', 'sender')
        dsn = f'dbname={db_name} user={db_user} host={db_host}'
        self.conn = psycopg2.connect(dsn)


    def register_message(self, subject, message):
        SQL = 'INSERT INTO emails (subject, message) VALUES (%s, %s)'
        cur = self.conn.cursor()
        cur.execute(SQL, (subject, message))
        self.conn.commit()
        cur.close()

        msg = {'subject': subject, 'message': message}
        self.queuenetwork.rpush('sender', json.dumps(msg))


        print('Message was registered !')

    def send(self):
        subject = request.forms.get('subject')
        message = request.forms.get('message')

        self.register_message(subject, message)

        return 'Queued messages ! Subject: {} Message: {}'.format(
            subject, message
        )

if __name__ == '__main__':
    sender = Sender()
    sender.run(host='0.0.0.0', port=8080, debug=True)