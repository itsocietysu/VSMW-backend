FROM python:3.6.6

WORKDIR /usr/src/app

COPY Requirements.txt ./
RUN pip install --no-cache-dir -r Requirements.txt

COPY vsmw/       ./vsmw/
COPY swagger-ui/ ./swagger-ui/

COPY server.py 		./server.py
COPY server_prod.py 		./server_prod.py
COPY config.json 	./config.json
COPY swagger.json 	./swagger.json
COPY VERSION 		./VERSION
COPY startup.sh         ./startup.sh
RUN chmod 777 ./startup.sh && \
    sed -i 's/\r//' ./startup.sh

RUN mkdir -p ./logs
RUN chmod 777 ./logs
VOLUME ./logs

RUN mkdir -p ./images
RUN chmod 777 ./images
VOLUME ./images

EXPOSE 4201

CMD ["./startup.sh"]
