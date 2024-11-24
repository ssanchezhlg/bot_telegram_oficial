import sys
import json
import requests
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from logging.handlers import TimedRotatingFileHandler
import time
from functools import wraps
from templates import get_html_template 
from datetime import datetime
import uuid

# Definir las variables
PORT = os.getenv('PORT')
bot_token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')
expected_token = os.getenv('EXPECTED_TOKEN')
proxy_address = os.getenv('proxy_address')

# Ruta de los logs
log_dir = '/srv/log'

def convert_port(port_value):
    """Convierte cualquier formato de puerto a entero"""
    return int(str(port_value).strip("'\""))

# Variable procesada para uso interno
PROCESSED_PORT = convert_port(PORT)

def clean_message(message):
    """Limpia el mensaje para guardarlo en una sola línea"""
    if isinstance(message, str):
        return ' '.join(message.replace('\n', ' ').replace('\r', ' ').split())
    return message

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.ip = getattr(record, 'ip', '-')
        record.request_id = getattr(record, 'request_id', '-')
        record.method = getattr(record, 'method', '-')
        record.path = getattr(record, 'path', '-')
        record.status_code = getattr(record, 'status_code', '-')
        record.process_time = getattr(record, 'process_time', '-')
        record.message_content = clean_message(getattr(record, 'message_content', ''))
        return True

# Configurar el log de la aplicación
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Agregar el filtro de contexto
logger.addFilter(ContextFilter())

# Crear el directorio de logs si no existe
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Crear el archivo de logs y configurar la rotación diaria
log_file = os.path.join(log_dir, "telegram-bot_servercentralizado.log")
handler = TimedRotatingFileHandler(log_file, when="midnight", backupCount=7)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s [%(ip)s] [%(request_id)s] '
    '[%(method)s %(path)s %(status_code)s] '
    '[%(process_time)s ms] '
    '%(message)s%(message_content)s'
))
logger.addHandler(handler)

# Asignar permisos al archivo de logs
os.chmod(log_file, 0o666)

# Verificar si se está utilizando un proxy
if proxy_address and proxy_address.strip():
    logger.info("Usando proxy", extra={'ip': 'SYSTEM', 'request_id': 'STARTUP'})
    proxies = {"https": proxy_address}
else:
    logger.info("No se está utilizando proxy", extra={'ip': 'SYSTEM', 'request_id': 'STARTUP'})
    proxies = None

class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.request_id = str(uuid.uuid4())[:8]
        self.start_time = time.time()
        self._path = None
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Sobrescribimos el método de logging para controlar los mensajes de consola"""
        try:
            current_path = getattr(self, 'path', '-')
            status_code = args[1] if len(args) > 1 else '-'
            
            # Filtrar mensajes de error SSL/TLS y bad requests
            if any(error in format % args for error in [
                'Bad request version',
                'Bad HTTP/0.9 request type',
                'code 400'
            ]):
                return  # No registrar estos errores
            
            # Solo registramos solicitudes exitosas y errores importantes
            if status_code == '200' or (status_code != '400'):
                # Log detallado al archivo
                logger.info(format % args, extra={
                    'ip': self.client_address[0],
                    'request_id': self.request_id,
                    'method': getattr(self, 'command', '-'),
                    'path': current_path,
                    'status_code': status_code,
                    'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
                })
                
                # Mensaje simplificado para la consola
                if current_path == '/health':
                    print(f"\033[92m✓\033[0m Health check desde {self.client_address[0]}")
                elif status_code == '200':
                    print(f"\033[94m→\033[0m {self.client_address[0]} - {getattr(self, 'command', '-')} {current_path}")
                elif status_code.startswith('4'):
                    print(f"\033[93m!\033[0m {self.client_address[0]} - Error {status_code}")
                elif status_code.startswith('5'):
                    print(f"\033[91m×\033[0m {self.client_address[0]} - Error {status_code}")

        except Exception as e:
            # Solo registrar errores reales de logging
            if not str(e).startswith(('Bad request', 'Bad HTTP')):
                logger.error(f"Error en logging: {str(e)}", extra={
                    'ip': self.client_address[0],
                    'request_id': self.request_id,
                    'method': '-',
                    'path': '-',
                    'status_code': '-',
                    'process_time': '-'
                })
                print(f"\033[91m×\033[0m Error de logging: {str(e)}")

    def handle_one_request(self):
        """Sobrescribimos el método para manejar mejor las conexiones incorrectas"""
        try:
            return super().handle_one_request()
        except ConnectionError:
            pass  # Ignoramos errores de conexión silenciosamente
        except Exception as e:
            if not str(e).startswith(('Bad request version', 'ValueError')):
                logger.error(f"Error en la solicitud: {str(e)}", extra={
                    'ip': self.client_address[0],
                    'request_id': self.request_id,
                    'method': getattr(self, 'command', '-'),
                    'path': getattr(self, 'path', '-'),
                    'status_code': '400',
                    'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
                })

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        logger.info("Solicitud OPTIONS procesada", extra={
            'ip': self.client_address[0],
            'request_id': self.request_id,
            'method': 'OPTIONS',
            'path': self.path,
            'status_code': '200',
            'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
        })

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_GET(self):
        if self.path == '/health':
            try:
                response = {
                    "status": "success",
                    "message": "Service is running"
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))
                logger.info("Health check realizado", extra={
                    'ip': self.client_address[0],
                    'request_id': self.request_id,
                    'method': 'GET',
                    'path': self.path,
                    'status_code': '200',
                    'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
                })
                return

            except Exception as e:
                logger.error(f"Error en health check: {str(e)}", extra={
                    'ip': self.client_address[0],
                    'request_id': self.request_id,
                    'method': 'GET',
                    'path': self.path,
                    'status_code': '500',
                    'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
                })
                self.send_error(500, "Internal Server Error")
                return

        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_cors_headers()
            self.end_headers()
            html_content = get_html_template({})
            self.wfile.write(html_content.encode('utf-8'))
            logger.info("Página principal servida", extra={
                'ip': self.client_address[0],
                'request_id': self.request_id,
                'method': 'GET',
                'path': self.path,
                'status_code': '200',
                'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
            })
            return
            
        else:
            self.send_error(404, "Not Found")
            logger.info("Ruta no encontrada", extra={
                'ip': self.client_address[0],
                'request_id': self.request_id,
                'method': 'GET',
                'path': self.path,
                'status_code': '404',
                'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
            })
            return

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            data = self.rfile.read(content_length)
            data_clean = data.decode('utf-8').replace('\n', '').replace('\r', '').replace('\t', '')
            data_json = json.loads(data_clean)

            text = data_json["message"].get("text", "")
            topic_id = data_json["message"].get("topic_id", "")
            file_path = data_json["message"].get("file_path", "")
            parse_mode = data_json["message"].get("parse_mode", "")

            # Verificar token
            token = data_json.get("token", "")
            if token != expected_token:
                logger.error("Token no válido", extra={
                    'ip': self.client_address[0],
                    'request_id': self.request_id,
                    'method': 'POST',
                    'path': self.path,
                    'status_code': '403',
                    'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
                })
                self.send_error(403, "Forbidden")
                return

            logger.info("Procesando mensaje", extra={
                'ip': self.client_address[0],
                'request_id': self.request_id,
                'method': 'POST',
                'path': self.path,
                'status_code': '200',
                'process_time': f"{(time.time() - self.start_time) * 1000:.2f}",
                'message_content': f" - Mensaje: {clean_message(text)} - Topic: {topic_id}"
            })

            if file_path and os.path.isfile(file_path):
                try:
                    # Enviar mensaje
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    params = {
                        "chat_id": chat_id,
                        "text": text,
                        "message_thread_id": topic_id
                    }
                    if parse_mode == "HTML":
                        params["parse_mode"] = "HTML"
                    
                    response = requests.post(url, data=params, proxies=proxies)
                    response.raise_for_status()
                    
                    # Enviar archivo
                    with open(file_path, 'rb') as file:
                        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                        files = {'document': file}
                        params = {
                            "chat_id": chat_id,
                            "message_thread_id": topic_id
                        }
                        
                        response = requests.post(url, files=files, data=params, proxies=proxies)
                        response.raise_for_status()
                        
                    logger.info("Mensaje y archivo enviados", extra={
                        'ip': self.client_address[0],
                        'request_id': self.request_id,
                        'method': 'POST',
                        'path': self.path,
                        'status_code': '200',
                        'process_time': f"{(time.time() - self.start_time) * 1000:.2f}",
                        'message_content': f" - Mensaje: {clean_message(text)} - Topic: {topic_id} - Archivo: {file_path}"
                    })

                except FileNotFoundError:
                    logger.error("Archivo no encontrado", extra={
                        'ip': self.client_address[0],
                        'request_id': self.request_id,
                        'method': 'POST',
                        'path': self.path,
                        'status_code': '404',
                        'process_time': f"{(time.time() - self.start_time) * 1000:.2f}",
                        'message_content': f" - Archivo: {file_path}"
                    })
                    self.send_error(404, "File Not Found")
                    return
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error en API Telegram: {str(e)}", extra={
                        'ip': self.client_address[0],
                        'request_id': self.request_id,
                        'method': 'POST',
                        'path': self.path,
                        'status_code': '500',
                        'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
                    })
                    self.send_error(500, "Internal Server Error")
                    return
            else:
                try:
                    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                    params = {
                        "chat_id": chat_id,
                        "text": text,
                        "message_thread_id": topic_id
                    }
                    if parse_mode == "HTML":
                        params["parse_mode"] = "HTML"
                    
                    response = requests.post(url, data=params, proxies=proxies)
                    response.raise_for_status()
                    logger.info("Mensaje enviado", extra={
                        'ip': self.client_address[0],
                        'request_id': self.request_id,
                        'method': 'POST',
                        'path': self.path,
                        'status_code': '200',
                        'process_time': f"{(time.time() - self.start_time) * 1000:.2f}",
                        'message_content': f" - Mensaje: {clean_message(text)} - Topic: {topic_id}"
                    })

                except requests.exceptions.RequestException as e:
                    logger.error(f"Error en API Telegram: {str(e)}", extra={
                        'ip': self.client_address[0],
                        'request_id': self.request_id,
                        'method': 'POST',
                        'path': self.path,
                        'status_code': '500',
                        'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
                    })
                    self.send_error(500, "Internal Server Error")
                    return

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode("utf-8"))

        except json.JSONDecodeError as e:
            logger.error(f"Error JSON: {str(e)}", extra={
                'ip': self.client_address[0],
                'request_id': self.request_id,
                'method': 'POST',
                'path': self.path,
                'status_code': '400',
                'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
            })
            self.send_error(400, "Bad Request - Invalid JSON")
        except Exception as e:
            logger.error(f"Error general: {str(e)}", extra={
                'ip': self.client_address[0],
                'request_id': self.request_id,
                'method': 'POST',
                'path': self.path,
                'status_code': '500',
                'process_time': f"{(time.time() - self.start_time) * 1000:.2f}"
            })
            self.send_error(500, "Internal Server Error")

def main():
    try:
        server_address = ('', PROCESSED_PORT)
        httpd = HTTPServer(server_address, Handler)

        logger.info("Servidor iniciado", extra={
            'ip': 'SYSTEM',
            'request_id': 'STARTUP',
            'method': '-',
            'path': '-',
            'status_code': '-',
            'process_time': '-',
            'message_content': f" - Puerto: {PROCESSED_PORT}"
        })
        
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Servidor detenido por usuario", extra={
            'ip': 'SYSTEM',
            'request_id': 'SHUTDOWN',
            'method': '-',
            'path': '-',
            'status_code': '-',
            'process_time': '-'
        })
        httpd.server_close()
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}", extra={
            'ip': 'SYSTEM',
            'request_id': 'STARTUP_ERROR',
            'method': '-',
            'path': '-',
            'status_code': '-',
            'process_time': '-'
        })
        sys.exit(1)

if __name__ == '__main__':
    main()