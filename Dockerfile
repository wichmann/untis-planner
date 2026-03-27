# untisplanner - Dockerfile

# use official Python runtime as base image
FROM python:3.14-slim

LABEL org.opencontainers.image.title="UntisPlanner"
LABEL org.opencontainers.image.description="Simple appointment planner using timetables from a WebUntis server"
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="wichmann@bbs-os-brinkstr.de"
LABEL org.opencontainers.image.licenses="MIT License"
#LABEL org.opencontainers.image.documentation="https://github.com/wichmann/untisplaner/blob/master/README.md"
#LABEL org.opencontainers.image.source="https://github.com/wichmann/untisplaner"

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# copy all necessary files into the image
COPY main.py /app/
COPY untisplanner.py /app/
COPY fullcalendar.py /app/
COPY fullcalendar.js /app/
COPY lib/ /app/lib/
COPY webuntis-config.ini /app/
COPY requirements.txt /app/
COPY README.md /app/
COPY LICENSE /app/
COPY pyproject.toml /app/

RUN pip install --no-cache-dir -r requirements.txt

# expose port used by NiceGUI (default: 8080)
EXPOSE 8080

# add health check using NiceGUI's built-in diagnostics endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/_nicegui/diagnostics || exit 1

ENTRYPOINT ["python", "main.py"]
