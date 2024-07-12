FROM python:3.12-slim
# Install required packages
RUN pip install requests

# Copy the Python script into the container
COPY main.py /main.py

# Set the entrypoint to the Python script
ENTRYPOINT ["python", "/main.py"]