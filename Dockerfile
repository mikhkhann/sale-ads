FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR sale-ads
COPY Pipfile Pipfile.lock ./
RUN pip install pipenv && pipenv install --system
COPY . .
