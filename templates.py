def get_html_template(stats):
    # Importar la variable PROCESSED_PORT del archivo principal
    from ServerCentralizadoTelegram import PROCESSED_PORT

    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <title>API Telegram - Centro de Control</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
    <style>
        :root {{
            --primary-color: #3b82f6;
            --primary-dark: #2563eb;
            --secondary-color: #1e40af;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --background-color: #f8fafc;
            --card-background: #ffffff;
            --text-color: #1e293b;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            line-height: 1.6;
            background-color: var(--background-color);
            color: var(--text-color);
        }}

        .container {{
            max-width: 1200px;
            margin: 2rem auto;
            padding: 0 1.5rem;
        }}

        .header {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            padding: 3rem 2rem;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.1);
            margin-bottom: 2rem;
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="rgba(255,255,255,0.1)"/></svg>') center/50% no-repeat;
            opacity: 0.1;
        }}

        .header h1 {{
            color: white;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            background-color: rgba(255,255,255,0.2);
            color: white;
            font-weight: 500;
            font-size: 0.875rem;
            backdrop-filter: blur(4px);
        }}

        .status-badge::before {{
            content: '';
            display: inline-block;
            width: 8px;
            height: 8px;
            background-color: var(--success-color);
            border-radius: 50%;
            margin-right: 0.5rem;
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
        }}

        .card {{
            background-color: var(--card-background);
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            margin-bottom: 2rem;
            border: 1px solid var(--border-color);
        }}

        .endpoint {{
            background-color: #f8fafc;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .endpoint:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 16px -4px rgba(0,0,0,0.1);
        }}

        .method {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}

        .method.post {{
            background-color: var(--success-color);
            color: white;
        }}

        .method.get {{
            background-color: var(--primary-color);
            color: white;
        }}

        code {{
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 1.5rem;
            border-radius: 8px;
            display: block;
            overflow-x: auto;
            margin: 1rem 0;
            font-family: 'Monaco', 'Consolas', monospace;
            font-size: 0.875rem;
            line-height: 1.7;
        }}

        .example-container {{
            margin: 1.5rem 0;
            padding: 1rem;
            background-color: white;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }}

        .example-title {{
            font-weight: 600;
            color: var(--text-color);
            margin-bottom: 0.5rem;
        }}

        .button-group {{
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }}

        button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            font-size: 0.875rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }}

        button:hover {{
            background-color: var(--primary-dark);
        }}

        ul {{
            list-style-type: none;
            padding-left: 0;
        }}

        ul li {{
            margin-bottom: 0.5rem;
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
        }}

        ul li code {{
            display: inline;
            padding: 0.25rem 0.5rem;
            margin: 0;
            border-radius: 4px;
            background-color: #f1f5f9;
            color: var(--text-color);
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 API Telegram - Centro de Control</h1>
            <span class="status-badge">Servidor Activo</span>
        </div>

        <div class="card">
            <h2>📡 Endpoints Disponibles</h2>
            
            <div class="endpoint">
                <h3><span class="method post">POST</span> Envío de Mensajes</h3>
                <p>Envía mensajes a un supergrupo de Telegram que utiliza Topics (Temas). Los mensajes se enviarán al topic específico configurado.</p>
                
                <div class="example-container">
                    <p class="example-title">📝 Mensaje de texto simple</p>
                    <code id="example1">{{
    "token": "b7f5c3a8d9e4f1a2b3c4d5e6f7a8b9c0",
    "message": {{
        "text": "Prueba de mensaje desde curl",
        "topic_id": "2"
    }}
}}</code>
                    <p class="example-title">🔧 Usando curl</p>
                    <code id="curl1">{PROCESSED_PORT}curl -X POST http://127.0.0.1:puerto \\
    -H "Content-Type: application/json" \\
    -d '{{
        "token": "b7f5c3a8d9e4f1a2b3c4d5e6f7a8b9c0",
        "message": {{
            "text": "Prueba de mensaje desde curl",
            "topic_id": "2"
        }}
    }}'</code>
                    <div class="button-group">
                        <button class="copy-button" data-target="example1">📋 Copiar JSON</button>
                        <button class="copy-button" data-target="curl1">🔄 Copiar curl</button>
                    </div>
                </div>

                <div class="example-container">
                    <p class="example-title">🎨 Mensaje con formato HTML</p>
                    <code id="example2">{{
    "token": "b7f5c3a8d9e4f1a2b3c4d5e6f7a8b9c0",
    "message": {{
        "text": "<b>Prueba</b>: Mensaje con <i>formato HTML</i>",
        "topic_id": "4",
        "parse_mode": "HTML"
    }}
}}</code>
                    <p class="example-title">🔧 Usando curl</p>
                    <code id="curl2">{PROCESSED_PORT}curl -X POST http://127.0.0.1:puerto \\
    -H "Content-Type: application/json" \\
    -d '{{
        "token": "b7f5c3a8d9e4f1a2b3c4d5e6f7a8b9c0",
        "message": {{
            "text": "<b>Prueba</b>: Mensaje con <i>formato HTML</i>",
            "topic_id": "4",
            "parse_mode": "HTML"
        }}
    }}'</code>
                    <div class="button-group">
                        <button class="copy-button" data-target="example2">📋 Copiar JSON</button>
                        <button class="copy-button" data-target="curl2">🔄 Copiar curl</button>
                    </div>
                </div>

                <div class="example-container">
                    <p class="example-title">📎 Mensaje con archivo adjunto</p>
                    <code id="example3">{{
    "token": "b7f5c3a8d9e4f1a2b3c4d5e6f7a8b9c0",
    "message": {{
        "text": "Enviando un archivo de prueba",
        "topic_id": "3",
        "file_path": "/ruta/al/archivo.txt"
    }}
}}</code>
                    <p class="example-title">🔧 Usando curl</p>
                    <code id="curl3">{PROCESSED_PORT}curl -X POST http://127.0.0.1:puerto \\
    -H "Content-Type: application/json" \\
    -d '{{
        "token": "b7f5c3a8d9e4f1a2b3c4d5e6f7a8b9c0",
        "message": {{
            "text": "Enviando un archivo de prueba",
            "topic_id": "3",
            "file_path": "/ruta/al/archivo.txt"
        }}
    }}'</code>
                    <div class="button-group">
                        <button class="copy-button" data-target="example3">📋 Copiar JSON</button>
                        <button class="copy-button" data-target="curl3">🔄 Copiar curl</button>
                    </div>
                </div>

                <div class="example-container">
                    <p class="example-title">📚 Parámetros disponibles</p>
                    <ul>
                        <li><code>token</code> Token de autenticación para la API (requerido)</li>
                        <li><code>text</code> Texto del mensaje a enviar (requerido)</li>
                        <li><code>topic_id</code> Número del topic/tema dentro del supergrupo (requerido, ej: 1, 2, 3...)</li>
                        <li><code>file_path</code> Ruta absoluta al archivo a enviar (opcional)</li>
                        <li><code>parse_mode</code> Usar "HTML" para formato con etiquetas HTML (opcional)</li>
                    </ul>
                </div>

                <div class="example-container">
                    <p class="example-title">ℹ️ Notas importantes</p>
                    <ul>
                        <li>El <code>topic_id</code> debe ser un número válido del tema en el supergrupo</li>
                        <li>Para mensajes HTML puedes usar: &lt;b&gt;, &lt;i&gt;, &lt;code&gt;, &lt;pre&gt;</li>
                        <li>Los archivos deben estar accesibles en el servidor de la API</li>
                        <li>La API está configurada en http://127.0.0.1:{PROCESSED_PORT}</li>
                    </ul>
                </div>
            </div>

            <div class="endpoint">
                <h3><span class="method get">GET</span> Estado del Servidor</h3>
                <p>Verifica el estado del servidor y sus componentes.</p>
                <code id="example4">{{
    "status": "health"
}}</code>
                <div class="button-group">
                    <button class="copy-button" data-target="example4">📋 Copiar respuesta</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        function copyToClipboard(text) {{
            const tempElement = document.createElement('textarea');
            tempElement.value = text;
            document.body.appendChild(tempElement);
            tempElement.select();
            document.execCommand('copy');
            document.body.removeChild(tempElement);
        }}

        document.addEventListener('DOMContentLoaded', function() {{
            document.querySelectorAll('.copy-button').forEach(button => {{
                button.addEventListener('click', function() {{
                    const targetId = this.getAttribute('data-target');
                    const codeElement = document.getElementById(targetId);
                    const textToCopy = codeElement.textContent;
                    
                    copyToClipboard(textToCopy);
                    
                    const originalText = this.textContent;
                    this.textContent = '✅ ¡Copiado!';
                    setTimeout(() => {{
                        this.textContent = originalText;
                    }}, 2000);
                }});
            }});
        }});
    </script>
</body>
</html>
"""