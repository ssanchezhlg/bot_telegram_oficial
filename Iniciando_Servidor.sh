#!/bin/bash

# prepare any message you want
date="$(date +"%A, %e de %B de %Y, %r" | sed 's/./\L&/g')"
hostname="$(hostname -f)"

# Aceptar el TOPIC_ID como argumento ID del Tema de Telegram
TOPIC_ID="3"

destinatarios="root@cristal.hlg.sld.cu,ssanchezhlg@infomed.sld.cu"

asunto="Iniciando Servidor [ $hostname ]"
message="El Servidor del [ $hostname ] se a Iniciando Correctamente \\n\\n¡Todo está listo para comenzar a trabajar! \n\n\n\n- Fecha y hora: $date \\n\\n\\n\\n¡Que tengas un excelente día! \n\nEl asistente virtual - Nodo Infomed Holguin\nEsta dirección electrónica está protegida contra spam bots"




# Ruta del archivo a enviar
FILE_PATH="/ruta/al/archivo/que/deseas/enviar"  # Cambia esta ruta al archivo que deseas enviar

## Envio de la notificación a Telegram
/home/python/servercentralizado/scripts/EnvioTelegram.sh "$message" "$TOPIC_ID" "$FILE_PATH"

echo -e "$message" | mailx -s "$asunto" $destinatarios
