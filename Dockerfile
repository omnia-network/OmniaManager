FROM python:3.7

WORKDIR /usr/src/app

EXPOSE 50500/tcp

COPY . .

RUN apt-get update
# install libraries for opencv
RUN apt-get install 'ffmpeg'\
    'libsm6'\ 
    'libxext6'  -y

#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

CMD [ "python", "./server.py" ]