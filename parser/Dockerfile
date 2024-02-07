FROM python:3.9

COPY /parser /app/parser
COPY db /app/db

RUN pip install -r /app/parser/requirements.txt

WORKDIR /app/parser

CMD ["python", "./run_parser.py"]
ENV PYTHONPATH /app/