# app/Dockerfile

FROM python:3.14-slim

LABEL org.opencontainers.image.title="UntisPlaner"
LABEL org.opencontainers.image.description="Simple appointment planner using timetables from a WebUntis server"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="wichmann@bbs-os-brinkstr.de"
LABEL org.opencontainers.image.licenses="MIT License"
#LABEL org.opencontainers.image.documentation="https://github.com/wichmann/untisplaner/blob/master/README.md"
#LABEL org.opencontainers.image.source="https://github.com/wichmann/untisplaner"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# copy all necessary files into the image
COPY app.py /app/
COPY untisplaner.py /app/
COPY requirements.txt /app/
COPY README.md /app/
COPY LICENSE /app/
COPY pyproject.toml /app/

RUN pip3 install -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
