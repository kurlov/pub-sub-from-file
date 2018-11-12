FROM python:3.7-alpine

WORKDIR /usr/src/app

COPY . .

RUN pip install -r requirements.txt

CMD [ "python", "./publisher.py" ]