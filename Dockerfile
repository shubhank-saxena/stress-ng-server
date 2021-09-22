FROM python:3.9.1-alpine

RUN pip install pipenv

RUN apk add --upgrade stress-ng

EXPOSE 8000 8000

LABEL Image for stress-ng server application

WORKDIR /app

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy --ignore-pipfile

COPY . .

CMD python server.py
