FROM python:3.11-slim

COPY requirements.txt .
COPY mm_api.py .

#RUN apt-get update && apt-get install -y git

RUN pip install -r requirements.txt

CMD ["python", "mm_api.py"]