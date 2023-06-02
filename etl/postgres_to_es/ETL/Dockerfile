# pull official base image
FROM python:3.9.6-alpine

# set work directory
WORKDIR /usr/src/ETL

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g'  /usr/src/ETL/entrypoint.sh
RUN chmod +x  /usr/src/ETL/entrypoint.sh

COPY . .
ENTRYPOINT ["/usr/src/ETL/entrypoint.sh"]
