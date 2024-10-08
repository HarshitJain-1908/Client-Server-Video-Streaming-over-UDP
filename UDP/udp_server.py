import cv2
import socket, time
import threading
import numpy as np
import base64

BUFF_SIZE = 1500
# Method responsible ffor handling the client_connection.
def handle_client(addr):
    # print('Client connected from:', addr)

    fps, st, frames_cnt, count = (0, 0, 20, 0)
    display = 0
    vid = cv2.VideoCapture("Rain.mp4")

    while vid.isOpened(): 

        ret, frame = vid.read()
        if not ret:
            # If the video is finished, break out of the loop
            break

        # Check if the frame is empty (which can happen if the camera is not working)
        if frame is None:
            print("Empty frame")
            continue
        
        # Fetching frame size. 
        # print(frame.size)
        
        # Encoding the frame and obtaining a buffer out of it. (buffer contains byte-array -> pixel values)
        encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
        # Calculate the size of the frame buffer.
        frame_size = len(buffer)
        timestamp = "{:.4f}".format(time.time())

        # Convert the frame size to a string and prefix it with a delimiter (e.g., '|')
        frame_size_str = "|" + timestamp + str(frame_size)

        # Send the frame size to the client before sending the frame data
        server_socket.sendto(frame_size_str.encode(), addr)
        
        # Updating the frame_displayed_count.
        display += 1

        # Splitting the frame_buffer into smaller chunks (of size chunk_size)
        chunk_size = 1500
        # Initializing a variable to track number of chunks sent for the current frame.
        chunks = 0

        # Iterating the buffer and sending each chunk one after another.
        for i in range(0, len(buffer), chunk_size):
            chunks += 1
            chunk = buffer[i:i + chunk_size]
            encoded_chunk = base64.b64encode(chunk)
            server_socket.sendto(encoded_chunk, addr)

        # Displaying the frame statistics at server side (for debugging purpose).
        # print("Frame -Time ", timestamp, "FRAME NUM - ", display ," ", frame_size, " SENT chunks - ", chunks)
        
        # Adding fps statistics in addition to the frame being sent.
        frame = cv2.putText(frame, 'FPS: ' + str(fps), (10, 40), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 255), 2)

        # Displaying the frame sent at server-side.
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
    
    # Sending end-frame to let the client know about it.
    end_string = "@" + str(display-1)
    server_socket.sendto(end_string.encode(), addr)

    # Logging connection termination event at server-side.
    server_socket.close()
    print('Successfully terminated connection with the client:', addr)

# Creating the server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
host_name = socket.gethostname()
host_ip = "192.168.233.1"
# host_ip = "192.168.45.244"
port = 12345
socket_address = (host_ip, port)

# Bind the socket to the address
server_socket.bind(socket_address)

# Listen for connections
print("Listening for connections on", host_ip)

# Accept a client connection --> Blocking Call
data, addr = server_socket.recvfrom(1024)
print('Connection from:', addr)
# print(data)

# Create a new thread to handle the client
client_thread = threading.Thread(target=handle_client, args=(addr,))
client_thread.start()