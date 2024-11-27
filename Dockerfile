FROM python:3.10.9-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv

COPY ./requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . /usr/src/app

RUN chmod +x /usr/src/app/scripts/run.sh

CMD ["/usr/src/app/scripts/run.sh"]