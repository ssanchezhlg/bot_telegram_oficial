FROM python:3.9-slim

# Agregar metadatos
LABEL mantenedor="Salvador Sánchez Sánchez <ssanchezhlg@gmail.com>"
LABEL version="1.3"
LABEL descripcion="Esta imagen no es mas que un API central para telegram el cual se encarga de darle salida a varios servidores que no tienen internet y se encuentran  en una red DMZ"

ENV PORT="9000"
ENV proxy_address="None"

WORKDIR /opt/app

COPY requirements.txt /opt/app/    
RUN pip install --no-cache-dir -r requirements.txt

# Simplificamos la instalación de dependencias
RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copiamos los archivos Python al directorio correcto
COPY ServerCentralizadoTelegram.py /opt/app/
COPY templates.py /opt/app/

VOLUME ["/srv/log"]

# Ejecutamos directamente el script Python
CMD ["python", "ServerCentralizadoTelegram.py"]