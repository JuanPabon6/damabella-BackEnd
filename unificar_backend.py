import os

# Archivo de salida donde quedará TODO consolidado
archivo_salida = "mapa_backend_damabella.md"

# Carpetas o archivos que queremos ignorar para no meter basura
IGNORAR = ['__pycache__', '.venv', 'venv', 'migrations', 'tests.py', 'settings.py', 'manage.py']

with open(archivo_salida, 'w', encoding='utf-8') as outfile:
    outfile.write("# MAPA DE ARQUITECTURA BACKEND - DAMABELLA\n\n")
    outfile.write("Este archivo contiene las rutas y vistas del backend para la integración móvil.\n\n")
    
    # Caminar por las carpetas del proyecto
    for root, dirs, files in os.walk('.'):
        # Filtrar carpetas ignoradas
        dirs[:] = [d for d in dirs if d not in IGNORAR and not d.startswith('.')]
        
        for file in files:
            # Solo nos interesan los controladores (views.py) y enrutadores (urls.py)
            if file in ['views.py', 'urls.py'] and not any(exp in root for exp in IGNORAR):
                ruta_completa = os.path.join(root, file)
                
                outfile.write(f"## ARCHIVO: {ruta_completa}\n")
                outfile.write("```python\n")
                
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    outfile.write(f"# Error leyendo archivo: {str(e)}\n")
                
                outfile.write("\n```\n\n")

print(f"¡Listo! Todo tu backend consolidado en: {archivo_salida}")