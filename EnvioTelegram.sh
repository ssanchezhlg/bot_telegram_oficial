#!/bin/bash

# ===========================================
# Requisitos de instalación:
# - jq: Procesador JSON para línea de comandos
#   Instalar con: sudo apt-get install jq
# - curl: Cliente para transferencia de datos
#   Instalar con: sudo apt-get install curl
# ===========================================
# Uso del script:
# ./EnvioTelegram.sh "mensaje" "topic_id" "ruta_archivo"
# - mensaje: Texto a enviar (obligatorio)
# - topic_id: ID del tema de Telegram (obligatorio)
# - ruta_archivo: Ruta del archivo a adjuntar (opcional)
# ===========================================

# Configuración general
BotServers=("127.0.0.1")
UrlBot="http://%s:8443"
BotToken="b7f5c3a8d9e4f1a2b3c4d5e6f7a8b9c0"
log_dir="/home/python/servercentralizado/logs"
log_file="$log_dir/message-bot_Client.log"
queue_file="$log_dir/message-queue.txt"
USE_HTML="true"
MAX_LOG_DAYS=30

# Variables de mensaje
message="$1"
TOPIC_ID="$2"
FILE_PATH="$3"

# Validación de argumentos
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "❌ Error: Faltan argumentos requeridos"
    echo "Uso: $0 \"mensaje\" \"topic_id\" [ruta_archivo]"
    echo "  - mensaje: Texto a enviar (obligatorio)"
    echo "  - topic_id: ID del tema (obligatorio)"
    echo "  - ruta_archivo: Ruta del archivo (opcional)"
    exit 1
fi

# Función para escribir logs de manera consistente
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    case "$level" in
        "INFO")  echo "$timestamp - ℹ️ $message" >> "$log_file" ;;
        "ERROR") echo "$timestamp - ❌ $message" >> "$log_file" ;;
        "WARN")  echo "$timestamp - ⚠️ $message" >> "$log_file" ;;
        "SUCCESS") echo "$timestamp - ✅ $message" >> "$log_file" ;;
        "DEBUG") echo "$timestamp - 🔍 $message" >> "$log_file" ;;
    esac
    
    if [ "$3" == "separator" ]; then
        echo "----------------------------------------" >> "$log_file"
    fi
}

# Función simplificada para limpiar logs antiguos
cleanup_old_logs() {
    find "$log_dir" -name "message-bot_Client.log.*" -type f -mtime +$MAX_LOG_DAYS -exec gzip {} \;
    find "$log_dir" -name "message-bot_Client.log.*.gz" -type f -mtime +$(($MAX_LOG_DAYS * 2)) -delete
}

# Función para verificar y rotar los logs diariamente
check_log_size() {
    local log_date=$(date -r "$log_file" +%Y%m%d 2>/dev/null)
    local current_date=$(date +%Y%m%d)
    
    if [ "$log_date" != "$current_date" ]; then
        local backup_name="$log_file.$log_date"
        gzip -c "$log_file" > "$backup_name.gz"
        
        if [ $? -eq 0 ]; then
            cat /dev/null > "$log_file"
            log_message "INFO" "Limpieza de logs antiguos completada" "separator"
        fi
    fi
}

# Función para verificar el estado del sistema de logs
check_log_status() {
    if [ ! -w "$log_dir" ]; then
        echo "Error: No hay permisos de escritura en $log_dir" >&2
        exit 1
    fi

    if [ -f "$log_file" ] && [ ! -w "$log_file" ]; then
        echo "Error: No hay permisos de escritura en $log_file" >&2
        exit 1
    fi
}

# Función para verificar si el servicio API está disponible
check_api_status() {
    local server="$1"
    local test_response
    test_response=$(curl -s -m 5 "$(printf $UrlBot "$server")/health" 2>/dev/null)
    if [ $? -eq 0 ]; then
        if [ "$(echo "$test_response" | jq -r '.status' 2>/dev/null)" == "success" ]; then
            return 0
        fi
    fi
    return 1
}

# Manejo de interrupciones
cleanup() {
    log_message "WARN" "Script interrumpido"
    exit 1
}

trap cleanup SIGINT SIGTERM

# Inicialización del sistema de logs
init_logging() {
    check_log_status
    
    if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir"
    fi

    if [ ! -f "$log_file" ]; then
        touch "$log_file"
    fi

    cleanup_old_logs
    check_log_size
}

# Inicializar logging
init_logging

# Verificar conexión
connected=false
for bot_server in "${BotServers[@]}"; do
    if ping -q -c 1 -W 1 "$bot_server" >/dev/null 2>&1; then
        if check_api_status "$bot_server"; then
            BotServer="$bot_server"
            connected=true
            log_message "SUCCESS" "Conectado al servidor: $bot_server"
            break
        else
            log_message "WARN" "Servidor accesible pero API no responde: $bot_server"
        fi
    else
        log_message "WARN" "Servidor no accesible: $bot_server"
    fi
done

# Función para procesar la cola de mensajes
process_message_queue() {
    if [ ! -f "$queue_file" ]; then
        return 0
    fi

    log_message "INFO" "Procesando mensajes en cola..."
    local temp_queue=$(mktemp)
    
    while IFS='|' read -r queued_message queued_topic queued_file || [ -n "$queued_message" ]; do
        if [ -n "$queued_message" ]; then
            log_message "INFO" "📤 Intentando enviar mensaje desde cola al tema: $queued_topic"
            
            if [ -n "$queued_file" ] && [ -f "$queued_file" ]; then
                if send_message "$queued_message" "true" "$queued_topic" "$queued_file" "queue"; then
                    continue
                fi
            else
                if send_message "$queued_message" "false" "$queued_topic" "" "queue"; then
                    continue
                fi
            fi
            echo "${queued_message}|${queued_topic}|${queued_file}" >> "$temp_queue"
        fi
    done < "$queue_file"
    
    mv "$temp_queue" "$queue_file"
    
    if [ ! -s "$queue_file" ]; then
        rm "$queue_file"
        log_message "SUCCESS" "Cola de mensajes procesada completamente"
    else
        log_message "WARN" "Algunos mensajes no pudieron ser enviados y permanecen en cola"
    fi
}

# Función para enviar mensaje
send_message() {
    local message_text="$1"
    local with_file="$2"
    local topic_id="${3:-$TOPIC_ID}"
    local file_path="${4:-$FILE_PATH}"
    local from_queue="${5:-}"
    local queue_indicator=""
    
    # Agregar indicador si el mensaje viene de la cola
    [ -n "$from_queue" ] && queue_indicator="[Mensaje desde cola] "

    if [ "$USE_HTML" == "true" ]; then
        if [ "$with_file" == "true" ]; then
            json_data=$(cat <<EOF
{
    "message": {
        "text": "<pre>$message_text</pre>",
        "parse_mode": "HTML",
        "topic_id": "$topic_id",
        "file_path": "$file_path"
    },
    "token": "$BotToken"
}
EOF
)
        else
            json_data=$(cat <<EOF
{
    "message": {
        "text": "<pre>$message_text</pre>",
        "parse_mode": "HTML",
        "topic_id": "$topic_id"
    },
    "token": "$BotToken"
}
EOF
)
        fi
    else
        if [ "$with_file" == "true" ]; then
            json_data=$(cat <<EOF
{
    "message": {
        "text": "$message_text",
        "topic_id": "$topic_id",
        "file_path": "$file_path"
    },
    "token": "$BotToken"
}
EOF
)
        else
            json_data=$(cat <<EOF
{
    "message": {
        "text": "$message_text",
        "topic_id": "$topic_id"
    },
    "token": "$BotToken"
}
EOF
)
        fi
    fi

    response=$(curl -s -m 10 -d "$json_data" \
        -H "Content-Type: application/json" \
        -X POST "$(printf $UrlBot "$BotServer")")

    if [ $? -ne 0 ] || [ -z "$response" ]; then
        echo "${message_text}|${topic_id}|${file_path}" >> "$queue_file"
        log_message "INFO" "Servidor no disponible. Mensaje guardado en cola"
        return 1
    fi

    if [ "$(echo "$response" | jq -r '.status')" == "success" ]; then
        log_message "SUCCESS" "${queue_indicator}Mensaje enviado exitosamente${with_file:+ con archivo '$file_path'} al tema ID: $topic_id"
        log_message "INFO" "${queue_indicator}Contenido del mensaje:\n$message_text"
        log_message "DEBUG" "${queue_indicator}Respuesta del servidor: $response" "separator"
        return 0
    else
        echo "${message_text}|${topic_id}|${file_path}" >> "$queue_file"
        log_message "INFO" "${queue_indicator}Error en respuesta del servidor. Mensaje guardado en cola"
        log_message "ERROR" "${queue_indicator}Error: $response" "separator"
        return 1
    fi
}

# Procesar mensaje
if $connected; then
    process_message_queue
    
    if [ -n "$FILE_PATH" ] && [ -f "$FILE_PATH" ]; then
        send_message "$message" "true"
    else
        while [ -n "$message" ]; do
            message_part="${message:0:4096}"
            message="${message:4096}"
            if [ -n "$message_part" ]; then
                send_message "$message_part" "false"
            fi
        done
    fi
else
    if [ -n "$message" ]; then
        echo "${message}|${TOPIC_ID}|${FILE_PATH}" >> "$queue_file"
        log_message "INFO" "Servidor no disponible. Mensaje guardado en cola"
        log_message "DEBUG" "Contenido del mensaje:\n$message" "separator"
    fi
fi

exit 0