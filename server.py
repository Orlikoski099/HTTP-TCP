import socket
import threading
import os
import uuid
import mimetypes

def handle_client(client_socket):
    request = client_socket.recv(1024)
    method, url, _ = request.split(b" ", 2)
    if method == b"GET":
        handle_get_request(url.decode("utf-8"), client_socket)
    elif method == b"POST":
        handle_post_request(client_socket, request)

def generate_image_links():
    image_links = []
    for filename in os.listdir("images"):
        if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):
            image_link = f'<a href="/images/{filename}">{filename}</a>'
            image_links.append(image_link)
    return "<br>".join(image_links)

def handle_get_request(url, client_socket):
    url = url.lstrip("/")
    if url == "":
        image_links = generate_image_links()
        html_content = f"""
        <html>
        <head><title>Página inicial</title></head>
        <body>
        <h1>Página inicial</h1>
        <p>Aqui estão as imagens disponíveis:</p>
        {image_links}
        <form method="post" enctype="multipart/form-data">
        Nome da imagem: <input type="text" name="filename"><br>
        Selecionar imagem: <input type="file" name="image"><br>
        <input type="submit" value="Enviar">
        </form>
        </body>
        </html>
        """
        html_content_encoded = html_content.encode("utf-8")
        client_socket.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
        client_socket.sendall(html_content_encoded)
    elif os.path.exists(url):
        with open(url, "rb") as image_file:
            image_data = image_file.read()
        client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n")
        client_socket.sendall(image_data)
    else:
        client_socket.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
        client_socket.send(b"<h1>404 Not Found</h1>")

def handle_post_request(client_socket, initial_request):
    request_data = initial_request
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        request_data += data

    header, body = request_data.split(b"\r\n\r\n", 1)
    boundary = header.split(b"boundary=")[-1].strip()
    boundary_bytes = b"--" + boundary

    parts = body.split(boundary_bytes)
    filename = None
    file_content = None

    for part in parts:
        if b"Content-Disposition" in part:
            headers, content = part.split(b"\r\n\r\n", 1)
            content = content.rsplit(b"\r\n", 1)[0]
            if b'name="filename"' in headers:
                filename = content.decode("utf-8").strip()
            elif b'name="image"' in headers:
                file_content = content

    if filename and file_content:
        mime_type = mimetypes.guess_type(filename)[0]
        if mime_type and mime_type.startswith("image/"):
            extension = mimetypes.guess_extension(mime_type)
            if extension:
                if not filename.endswith(extension):
                    filename += extension
            image_path = os.path.join("images", filename)
            with open(image_path, "wb") as image_file:
                image_file.write(file_content)
            client_socket.send(b"HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n")
        else:
            client_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            client_socket.send(b"<h1>400 Bad Request</h1>")
    else:
        client_socket.send(b"HTTP/1.1 400 Bad Request\r\n\r\n")
        client_socket.send(b"<h1>400 Bad Request</h1>")

def start_server(host, port):
    if not os.path.exists("images"):
        os.makedirs("images")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[*] Listening on {host}:{port}")

    while True:
        client_socket, _ = server_socket.accept()
        print(f"[*] Accepted connection from {client_socket.getpeername()}")

        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    HOST = "127.0.0.1"
    PORT = 8080

    start_server(HOST, PORT)
