FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install uv && uv sync

EXPOSE 2009

CMD ["uv", "run", "python", "main.py"]
