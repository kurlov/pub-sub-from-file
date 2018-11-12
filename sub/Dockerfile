FROM python:3.7-alpine

WORKDIR /usr/src/app

COPY . .

RUN apk add --no-cache gcc musl-dev

RUN pip install -r requirements.txt

CMD [ "python", "./subscriber.py" ]