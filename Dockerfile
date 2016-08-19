FROM ubuntu:latest
MAINTAINER Geremy Gibson "evtbbw@yhaoo.com"
COPY ./app /app/app
COPY ./run.py /app
COPY ./requirements.txt /app
WORKDIR /app
RUN apt-get update -y && apt-get install -y python-pip python-dev build-essential && pip install --upgrade pip && pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["run.py"]
