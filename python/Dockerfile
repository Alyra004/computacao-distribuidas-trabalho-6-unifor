FROM python:3.12-slim

WORKDIR /app

# Instala dependências Python
COPY python/requirements.txt /app/python/requirements.txt
RUN pip install --no-cache-dir -r /app/python/requirements.txt

# Copia contratos compartilhados (seed, wsdl, proto) e código Python
COPY contracts /app/contracts
COPY python /app/python

ENV PYTHONPATH=/app/python
ENV SEED_DATA_PATH=/app/contracts/seed/initial_data.json
ENV WSDL_PATH=/app/contracts/soap/streaming.wsdl

# Gera os stubs gRPC dentro de /app/python/grpc_api
RUN python -m grpc_api.generate_proto

EXPOSE 8001 8002 8003 50051

CMD ["uvicorn", "rest_api.main:app", "--host", "0.0.0.0", "--port", "8001"]
