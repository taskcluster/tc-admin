# %ARG PYTHON_VERSION
FROM python:$PYTHON_VERSION-alpine
MAINTAINER Dustin Mitchell <dustin@mozilla.com>

ADD requirements.txt make_decision.py /
RUN pip install -r /requirements.txt

CMD [ "python", "/make_decision.py" ]
