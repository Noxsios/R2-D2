# WORK IN PROGRESS DO NOT USE YET

FROM registry1.dso.mil/ironbank/opensource/python/python39:latest

WORKDIR /cli

USER root

RUN yum install git -y -q >/dev/null 2>&1

USER python

COPY --chown=python . .

ENV POETRY_VERSION=1.1.13

RUN pip3 install .

ENTRYPOINT [ "poetry run r2d2" ]