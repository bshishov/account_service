# Python 3.6 using Debian Jessie
FROM python:3.6-jessie

MAINTAINER Boris Shishov <borisshishov@gmail.com>

ENV PYTHONUNBUFFERED 1
ENV PORT=8089
ENV PROJECT_PATH=/opt/account_service
ENV PROJECT_LOGS_ROOT=/var/log/account_service

RUN echo "Image project path: $PROJECT_PATH"

RUN mkdir -p -v $PROJECT_PATH

# Copy src files (entrypoint included)
COPY ./ $PROJECT_PATH
WORKDIR $PROJECT_PATH

# Upgrade pip and install all required python dependencies
RUN pip install --no-cache-dir -r $PROJECT_PATH/requirements.txt

# Project port (both for wsgi setup or for http setup)
EXPOSE $PORT

# Setup the docker entrypoint
# NOTE: It should be with LF (unix) line-endings
COPY ./docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["help"]
