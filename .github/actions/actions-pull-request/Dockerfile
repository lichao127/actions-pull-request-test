FROM python:3.12-slim

# Install required packages
RUN apt-get update && apt-get install -y git
RUN pip install requests

COPY main.py /main.py
COPY .git* /
RUN ls -al
RUN git status

# Set the entrypoint to the Python script
ENTRYPOINT ["python", "/main.py"]
