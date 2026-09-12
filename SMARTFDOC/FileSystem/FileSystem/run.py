"""
Скрипт для запуска приложения
"""
from backend.app import app

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("=" * 50)
    print("Запуск сервера системы управления документами")
    print("=" * 50)
    print(f"Сервер доступен по адресам:")
    print(f"  - http://localhost:5000")
    print(f"  - http://127.0.0.1:5000")
    print(f"  - http://{local_ip}:5000")
    print(f"API доступен по адресу: http://localhost:5000/api")
    print("=" * 50)
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)



