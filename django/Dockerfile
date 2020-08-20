FROM python:3.8-buster

# The enviroment variable ensures that the python output is set straight
# to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# create root directory for our project in the container
RUN mkdir /django

# create scrapy subdir
RUN mkdir /django/scraper

# Pip dependency Twisted needs gcc
RUN apt-get update
RUN apt-get install -y gcc

# Set the working directory to /django
WORKDIR /django

# Install needed packages for DJANGO specified in requirements.txt
ADD ./requirements.txt .
RUN pip install -r requirements.txt

# Install needed packages for SCRAPY specified in requirements.txt
ADD ./scraper/requirements.txt ./scraper
RUN pip install -r scraper/requirements.txt

RUN pip install git+https://github.com/ArneDefauw/dkpro-cassis@master