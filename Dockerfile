FROM python:3.8-slim-buster
#ENV PYTHONUNBUFFERED=1
WORKDIR /IP_WEB_APP

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 9000

CMD [ "python3", "app.py"]