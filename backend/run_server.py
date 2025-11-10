"""
Script para iniciar el servidor FastAPI
"""
import uvicorn
import socket
import sys

def is_port_in_use(port):
    """Verifica si un puerto está en uso"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_free_port(start_port=8000, max_attempts=10):
    """Encuentra un puerto libre empezando desde start_port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None

if __name__ == "__main__":
    # Configuración del servidor
    DEFAULT_PORT = 8000
    HOST = "127.0.0.1"  # localhost - más seguro y evita problemas de permisos en Windows
    
    # Verificar si el puerto está en uso
    if is_port_in_use(DEFAULT_PORT):
        print(f"⚠️  El puerto {DEFAULT_PORT} está en uso.")
        free_port = find_free_port(DEFAULT_PORT + 1)
        if free_port:
            print(f"✅ Usando puerto alternativo: {free_port}")
            PORT = free_port
        else:
            print(f"❌ No se encontró un puerto libre. Cierra otros procesos o cambia el puerto manualmente.")
            sys.exit(1)
    else:
        PORT = DEFAULT_PORT
    
    print(f"🚀 Iniciando servidor en http://{HOST}:{PORT}")
    print(f"📚 Documentación disponible en http://{HOST}:{PORT}/docs")
    
    try:
        uvicorn.run(
            "app.main:app",
            host=HOST,
            port=PORT,
            reload=True,  # Auto-reload en desarrollo
            log_level="info"
        )
    except PermissionError:
        print(f"\n❌ Error de permisos en el puerto {PORT}")
        print(f"💡 Soluciones:")
        print(f"   1. Cierra otros procesos que usen el puerto {PORT}")
        print(f"   2. Ejecuta PowerShell como Administrador")
        print(f"   3. Cambia el puerto manualmente editando este archivo")
        sys.exit(1)
    except OSError as e:
        if "10013" in str(e) or "WinError 10013" in str(e):
            print(f"\n❌ Error de permisos de socket (WinError 10013)")
            print(f"💡 Soluciones:")
            print(f"   1. Cierra otros procesos que usen el puerto {PORT}")
            print(f"   2. Ejecuta PowerShell como Administrador")
            print(f"   3. Verifica el firewall de Windows")
            print(f"   4. Cambia el puerto manualmente editando este archivo")
        else:
            print(f"\n❌ Error: {e}")
        sys.exit(1)

