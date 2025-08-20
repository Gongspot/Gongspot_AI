FROM python:3.10-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

RUN pip install --upgrade pip pipenv && \
    pipenv install --system --deploy

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]