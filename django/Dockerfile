FROM python:3.8-slim-buster

# The enviroment variable ensures that the python output is set straight
# to the terminal without buffering it first
ENV PYTHONUNBUFFERED 1

# Pip dependency Twisted needs gcc
RUN apt-get update
RUN apt-get install -y gcc

# create root directory for our project in the container
RUN mkdir /django

# Set the working directory to /django
WORKDIR /django

# Install any needed packages specified in requirements.txt
ADD ./requirements.txt .
RUN pip install -r requirements.txt

