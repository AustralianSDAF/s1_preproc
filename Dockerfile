FROM mundialis/esa-snap:latest

WORKDIR /app
COPY requirements.txt /app/env/

RUN pip install -r /app/env/requirements.txt
COPY . .

ENTRYPOINT [ "python3", "main.py" ]