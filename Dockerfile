FROM python:3.11-slim
WORKDIR /app
COPY cloud/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -m -u 1000 solune
COPY --chown=solune:solune cloud/app.py ./app.py
COPY --chown=solune:solune app/src/main/assets/index.html ./index.html
USER solune
EXPOSE 7860
CMD ["sh","-c","exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
