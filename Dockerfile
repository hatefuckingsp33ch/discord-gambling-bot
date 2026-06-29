FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install discord.py
CMD ["python", "main.py"]
