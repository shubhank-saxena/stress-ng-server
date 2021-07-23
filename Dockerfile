FROM python:3.9.1-alpine

RUN ["pip3", "install", "pipenv"]

LABEL Image for stress-ng server application

WORKDIR /app

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy --ignore-pipfile

COPY . .

CMD python main.py