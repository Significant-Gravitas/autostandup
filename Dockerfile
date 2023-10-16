# Download Cloud SQL Proxy
FROM gcr.io/cloud-builders/wget as builder
RUN wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
RUN chmod +x cloud_sql_proxy

# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy Cloud SQL Proxy from the builder image
COPY --from=builder /cloud_sql_proxy /app/cloud_sql_proxy

# Overwrite requirements.txt
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 80 available to the world outside this container
EXPOSE 80

# Start Cloud SQL Proxy and your application
CMD ./cloud_sql_proxy -instances=standup-bot-402021:us-west2:myinstance=tcp:3306 & python bot.py
