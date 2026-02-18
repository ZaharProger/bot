FROM python:3.13-alpine

WORKDIR /bot

RUN apk add --no-cache gcc musl-dev libc-dev

COPY requirements.txt ./
COPY main.py ./
COPY src/ ./src/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]