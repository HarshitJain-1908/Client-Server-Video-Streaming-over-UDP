import cv2
import socket
import numpy as np
import time
import base64
import threading
import queue

BUFFER_SIZE = 3000  # Increase buffer size

# Create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Server address and port
server_ip = "192.168.233.1"  # Replace with the server's IP address
# server_ip = "192.168.74.1"  # Replace with the server's IP address
server_port = 12345
server_addr_port = (server_ip, server_port)

message = "I'm a Client!!"
encoded_mssg = str.encode(message)
client_socket.sendto(encoded_mssg, server_addr_port)

frame_data = b""
sample_frame_size_received = False
sample_frame_size = 0
expected_frame_size = 0

fps, st, frame_cnt, count = (0, 0, 20, 0)
displays = 0
chunks = 0
num = 0
timestamp = ""

# Create a queue for frame data
frame_queue = queue.Queue()

# Function to process frames
def process_frames():
    global fps, st, count
    while True:
        if not frame_queue.empty():
            complete_frame_data = frame_queue.get()
            try:
                frame = cv2.imdecode(np.frombuffer(complete_frame_data, dtype=np.uint8), cv2.IMREAD_COLOR)
            except cv2.error as e:
                print(f"Error decoding frame: {e}")
                continue
            
            if frame is not None:
                # print("Displayed frame - ", displays)
                frame = cv2.putText(frame, 'FPS: ' + str(fps), (10, 40), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 255), 2)
                # frame = cv2.resize(frame, (1280, 720))  # Resize frames before displaying
                cv2.imshow("RECEIVING AT CLIENT", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            client_socket.close()
            break

# Create a thread for processing frames
processing_thread = threading.Thread(target=process_frames)
processing_thread.start()

# Function to receive data and manage frames
def receive_data():
    global frame_data, expected_frame_size, displays, fps, st, count, chunks, num, timestamp
    while True:
        packet, ret = client_socket.recvfrom(BUFFER_SIZE)
        if packet.startswith(b'|'):
            # Parse the timestamp from the frame info
            timestamp = packet[1:16].decode()
            # displays += 1
            frame_size = int(packet[16:].decode())
            num = packet[:3].decode()
            expected_frame_size = frame_size
            sample_frame_size_received = True
            frame_data = b""
            chunks = 0
            print("Received frame at timestamp:", timestamp)
            continue
        else:
            data = base64.b64decode(packet)
            frame_data += data
            chunks += 1
        
        if len(frame_data) >= expected_frame_size:
            displays += 1
            print("Time - ", timestamp, "Curr-Time ", str(time.time()), " Frame NUM - ", displays, " chunks - ", chunks, " expec_frame_size - ", expected_frame_size, " frame_data - ", len(frame_data))
            if count == frame_cnt:
                try:
                    fps = round(frame_cnt / (time.time() - st))
                    st = time.time()
                    count = 0
                except:
                    pass
                
            count += 1
            
            frame_queue.put(frame_data)
            
            frame_data = b""

# Create a thread for receiving data.
receive_thread = threading.Thread(target=receive_data)
receive_thread.start()

while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Close the client socket when done.
client_socket.close()
cv2.destroyAllWindows()
