FROM ubuntu:18.04

RUN apt install -y openjdk-17-jdk
#RUN apt-get install -y python3

RUN mkdir -p /docdochae/home

ENV FILE_SERVER_URL 192.168.0.25:8144
ENV HOME /DocDocHae/home
ENV OCR_SERVER_URL hq.epapyrus.com:11057

ADD ./module /DocDocHae/home/module
ADD ./start.sh /DocDocHae/home/
ADD ./DocDocHae-1.0.0.jar /DocDocHae/