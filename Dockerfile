FROM python:3.11.11-alpine

RUN apk update && apk add -y --no-install-recommends --no-cache libmagic

RUN mkdir app
COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]