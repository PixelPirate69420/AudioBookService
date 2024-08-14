import os
import socket
import threading
import urllib.parse
import mimetypes

BASE_DIRECTORY = 'audiobooklib'


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return "Unable to determine local IP address"


def list_directory_contents(path):
    items = []
    if os.path.isdir(path):
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            relative_path = os.path.relpath(full_path, BASE_DIRECTORY)
            if os.path.isdir(full_path):
                item_link = urllib.parse.quote(relative_path) + '/'
                items.append({'name': entry, 'link': item_link, 'type': 'directory'})
            else:
                item_link = urllib.parse.quote(relative_path)
                items.append({'name': entry, 'link': item_link, 'type': 'file'})
    return items


def search_directory(base_path, search_term):
    results = []
    search_term_lower = search_term.lower()
    for root, dirs, files in os.walk(base_path):
        for name in dirs + files:
            if search_term_lower in name.lower():
                full_path = os.path.join(root, name)
                relative_path = os.path.relpath(full_path, BASE_DIRECTORY)
                item_type = 'directory' if os.path.isdir(full_path) else 'file'
                match_score = name.lower().count(search_term_lower) / max(len(name), len(search_term))
                results.append({'name': name, 'link': urllib.parse.quote(relative_path), 'type': item_type,
                                'match_score': match_score})
    return results


def generate_html_response(items, search_term, relative_path=""):
    is_empty = not items
    parent_directory = '/'.join(relative_path.split('/')[:-1]) if relative_path else ''

    items_html = ""
    for item in items:
        score = f" (Score: {item['match_score']:.2f})" if search_term else ""
        download_button = ""
        listen_button = ""
        folder_emoji = "📁" if item["type"] == "directory" else ""

        if item["type"] == "file":
            download_button = f"<button class='button download-button' onclick=\"window.location.href='/download/{item['link']}';\">Download</button>"
            if item["link"].endswith(".mp3"):
                listen_button = f"<button class='button listen-button' onclick=\"window.location.href='/listen/{item['link']}';\">Listen</button>"

        items_html += f'''
        <div class="card">
            <div class="card-header">
                <a href="/{item["link"]}" class="card-link">{item["name"]}{score}</a>
            </div>
            <div class="card-buttons">
                {download_button}
                {listen_button}
            </div>
            <span class='folder-emoji'>{folder_emoji}</span>
        </div>
        '''

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AudioBookService</title>
        <style>
            /* Basic Reset */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: Arial, sans-serif;
                color: #333;
                background-color: #e9ecef;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }}
            header {{
                background-color: #343a40;
                color: white;
                padding: 1em;
                text-align: center;
            }}
            .search-form {{
                display: flex;
                justify-content: center;
                margin-top: 1em;
            }}
            .search-form input[type="text"] {{
                padding: 0.5em;
                border: 1px solid #ced4da;
                border-radius: 4px 0 0 4px;
                width: 300px;
                max-width: 100%;
            }}
            .search-form button {{
                padding: 0.5em 1em;
                border: 1px solid #ced4da;
                border-radius: 0 4px 4px 0;
                background-color: #007bff;
                color: white;
                cursor: pointer;
                font-size: 1em;
            }}
            .search-form button:hover {{
                background-color: #0056b3;
            }}
            main {{
                flex: 1;
                padding: 2em;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .container {{
                width: 90%;
                max-width: 1200px;
            }}
            .cards {{
                display: flex;
                flex-direction: column;
                gap: 1em;
                width: 100%;
                max-width: 1200px;
                margin: auto;
            }}
            .card {{
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 1em;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                position: relative;
                width: 100%;
                max-width: 350px;
                min-height: 80px; /* Adjust height for the card */
                display: flex;
                flex-direction: column;
                align-items: center;
                box-sizing: border-box;
            }}
            .card a {{
                text-decoration: none;
                color: #007bff;
                font-size: 1em;
                display: block;
                margin-bottom: 0.5em;
            }}
            .card a:hover {{
                text-decoration: underline;
            }}
            .card-buttons {{
                display: flex;
                justify-content: center;
                gap: 0.5em;
                margin-top: 0.5em;
            }}
            .button {{
                display: inline-block;
                padding: 0.5em 1em;
                color: white;
                border-radius: 4px;
                text-decoration: none;
                font-size: 0.9em;
                cursor: pointer;
                border: none;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            .download-button {{
                background-color: #dc3545;
            }}
            .download-button:hover {{
                background-color: #c82333;
            }}
            .listen-button {{
                background-color: #66bb6a; /* Brighter green */
            }}
            .listen-button:hover {{
                background-color: #4caf50;
            }}
            .folder-emoji {{
                font-size: 1.5em;
                display: block;
                margin-top: 0.5em;
            }}
            footer {{
                background-color: #343a40;
                color: white;
                padding: 1em;
                text-align: center;
                width: 100%;
            }}
            .empty {{
                text-align: center;
                color: #666;
                font-size: 1.2em;
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>AudioBookService</h1>
        </header>
        <main>
            <div class="container">
                <div class="search-form">
                    <form method="get" action="/">
                        <input type="text" name="search" placeholder="Search..." value="{search_term}">
                        <button type="submit">Search</button>
                    </form>
                </div>
                <div class="cards">
                    {items_html if not is_empty else "<p class='empty'>Empty folder</p>"}
                </div>
            </div>
        </main>
        <footer>
            <p>&copy; 2024 AudioBookService</p>
        </footer>
    </body>
    </html>
    '''


def handle_client_request(client_socket, request):
    try:
        parts = request.split(' ')
        path = parts[1] if len(parts) > 1 else '/'
        search_term = ""
        query_index = path.find('?search=')
        if query_index != -1:
            search_term = urllib.parse.unquote(path[query_index + 8:])
            relative_path = path[:query_index]
        else:
            relative_path = path

        normalized_path = os.path.normpath(os.path.join(BASE_DIRECTORY, relative_path.strip('/')))
        if not normalized_path.startswith(BASE_DIRECTORY):
            normalized_path = os.path.join(BASE_DIRECTORY, relative_path.strip('/'))

        if os.path.isdir(normalized_path):
            if search_term:
                items = search_directory(BASE_DIRECTORY, search_term)
            else:
                items = list_directory_contents(normalized_path)

            response_body = generate_html_response(items, search_term, relative_path=relative_path.lstrip('/'))
            response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html\r\n"
                    "Connection: close\r\n"
                    "\r\n" +
                    response_body
            )
            client_socket.sendall(response.encode('utf-8'))

        elif os.path.isfile(normalized_path):
            mime_type, _ = mimetypes.guess_type(normalized_path)
            if mime_type is None:
                mime_type = "application/octet-stream"  # Default MIME type for unknown files

            response_headers = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Type: {mime_type}\r\n"
                "Connection: close\r\n"
                "\r\n"
            )
            client_socket.sendall(response_headers.encode('utf-8'))
            with open(normalized_path, 'rb') as file:
                while (chunk := file.read(1024)):
                    client_socket.sendall(chunk)
        elif path.startswith('/download/'):
            file_path = os.path.normpath(
                os.path.join(BASE_DIRECTORY, urllib.parse.unquote(path[len('/download/'):].strip('/'))))
            if os.path.isfile(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type is None:
                    mime_type = "application/octet-stream"

                response_headers = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {mime_type}\r\n"
                    f"Content-Disposition: attachment; filename=\"{os.path.basename(file_path)}\"\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )
                client_socket.sendall(response_headers.encode('utf-8'))
                with open(file_path, 'rb') as file:
                    while (chunk := file.read(1024)):
                        client_socket.sendall(chunk)
            else:
                response_body = "<h1>404 Not Found</h1>"
                response = (
                        "HTTP/1.1 404 Not Found\r\n"
                        "Content-Type: text/html\r\n"
                        "Connection: close\r\n"
                        "\r\n" +
                        response_body
                )
                client_socket.sendall(response.encode('utf-8'))
        elif path.startswith('/listen/'):
            file_path = os.path.normpath(
                os.path.join(BASE_DIRECTORY, urllib.parse.unquote(path[len('/listen/'):].strip('/'))))
            if os.path.isfile(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                if mime_type is None:
                    mime_type = "application/octet-stream"

                response_headers = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {mime_type}\r\n"
                    "Connection: close\r\n"
                    "\r\n"
                )
                client_socket.sendall(response_headers.encode('utf-8'))
                with open(file_path, 'rb') as file:
                    while (chunk := file.read(1024)):
                        client_socket.sendall(chunk)
            else:
                response_body = "<h1>404 Not Found</h1>"
                response = (
                        "HTTP/1.1 404 Not Found\r\n"
                        "Content-Type: text/html\r\n"
                        "Connection: close\r\n"
                        "\r\n" +
                        response_body
                )
                client_socket.sendall(response.encode('utf-8'))
        else:
            response_body = "<h1>404 Not Found</h1>"
            response = (
                    "HTTP/1.1 404 Not Found\r\n"
                    "Content-Type: text/html\r\n"
                    "Connection: close\r\n"
                    "\r\n" +
                    response_body
            )
            client_socket.sendall(response.encode('utf-8'))
    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()


def start_server():
    local_ip = get_local_ip()
    port = 8080
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((local_ip, port))
    server_socket.listen(5)
    print(f"Server listening on http://{local_ip}:{port}")

    while True:
        client_socket, _ = server_socket.accept()
        request = client_socket.recv(1024).decode('utf-8')
        if request:
            threading.Thread(target=handle_client_request, args=(client_socket, request)).start()


if __name__ == "__main__":
    start_server()
