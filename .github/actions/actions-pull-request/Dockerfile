FROM python:3.12-slim

# Install required packages
RUN apt-get update && apt-get install -y git
RUN pip install requests

# Copy the Python script into the container
#COPY main.py /main.py
COPY ** /
RUN ls -al /

# Set the entrypoint to the Python script
ENTRYPOINT ["python", "/main.py"]
