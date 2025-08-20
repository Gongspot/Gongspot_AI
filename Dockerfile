FROM python:3.10-slim-bullseye

WORKDIR /app

# 종속성 설치 캐시 활용
COPY Pipfile Pipfile.lock ./

RUN pip install pipenv
RUN pipenv sync --system --dev

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]