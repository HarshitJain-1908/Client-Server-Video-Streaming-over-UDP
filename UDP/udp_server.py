import cv2
import imutils
import socket, time
import threading
import numpy as np
import base64

BUFF_SIZE = 1500
# Function to handle a client connection
def handle_client(client_socket, addr):
    print('Client connected from:', addr)

    # one = 0
    fps, st, frames_cnt, count = (0, 0, 20, 0)
    # WIDTH = 400
    vid = cv2.VideoCapture("Rain.mp4")
    display = 0
    while vid.isOpened(): # and display <= 5:
        ret, frame = vid.read()
        if not ret:
            # If the video is finished, break out of the loop
            break

        # Check if the frame is empty (which can happen if the camera is not working)
        if frame is None:
            print("Empty frame")
            continue
        # print("ACTUAL FRAME SIZE:", frame.size)
        # frame = imutils.resize(frame, width=WIDTH)
        encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
        # print(encoded)    // True
        # print("BUFFER\n", buffer) // a list of pixel values
        # data = base64.b64encode(buffer)
        # print("DATA LEN - ", len(buffer))
        # Calculate the size of the frame
        frame_size = len(buffer)
        timestamp = "{:.4f}".format(time.time())

        # Convert the frame size to a string and prefix it with a delimiter (e.g., '|')
        # frame_size_str = "|" + str(display) + str(frame_size)

        frame_size_str = "|" + timestamp + str(frame_size)

        # Send the frame size to the client before sending the frame data
        server_socket.sendto(frame_size_str.encode(), addr)
        
        display += 1
        # print("FRAME NUM - ", display ," ", frame_size)
        # Split the data into smaller chunks (e.g., 1500 bytes each)
        chunk_size = 1100
        chunks = 0
 
        Set = set()
        for i in range(0, len(buffer), chunk_size):
            chunks += 1
            chunk = buffer[i:i + chunk_size]
            # chunk = str(chunks) + "|" + chunk.decode()
            encoded_chunk = base64.b64encode(chunk)
            # print("Encoded chunk len - ", len(encoded_chunk))
            Set.add(len(encoded_chunk))
            server_socket.sendto(encoded_chunk, addr)

        print("Frame -Time ", timestamp, "FRAME NUM - ", display ," ", frame_size, " SENT chunks - ", chunks, " - ", Set)
        
        frame = cv2.putText(frame, 'FPS: ' + str(fps), (10, 40), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 255), 2)
        # print(frame.size)
        # print(frame.size)
        # frame = cv2.resize(frame, (640, 480))

        # Display the frame on the server side
        cv2.imshow('Server Video', frame)
        key = cv2.waitKey(1)  # Update the display
        if key == ord('q'):
            server_socket.close()
            break

        if count == frames_cnt:
            try:
                fps = round(frames_cnt / (time.time() - st))
                st = time.time()
                count = 0
            except:
                pass
        count += 1

    cv2.destroyAllWindows()
    vid.release()
    print('Client disconnected from:', addr)


# Creating the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
host_name = socket.gethostname()
host_ip = "192.168.233.1"
# host_ip = "192.168.74.1"
port = 12345
socket_address = (host_ip, port)

# Bind the socket to the address
server_socket.bind(socket_address)

# Listen for connections
print("Listening for connections on", host_ip)

while True:
    # Accept a client connection
    data, addr = server_socket.recvfrom(1024)
    print('Connection from:', addr)
    print(data)

    # Create a new thread to handle the client
    client_thread = threading.Thread(target=handle_client, args=(server_socket, addr))
    client_thread.start()
