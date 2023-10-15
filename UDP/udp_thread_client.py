import cv2
import socket
import numpy as np
import time
import base64
import threading
import queue
import matplotlib.pyplot as plt

BUFFER_SIZE = 2000  

# Creating a socket for client. (UDP socket)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Defining server's address
server_ip = "192.168.233.1"  
server_port = 12345
server_addr_port = (server_ip, server_port)

# Initiating the connection with server_socket
client_socket.sendto("Initial Message".encode(), server_addr_port)

frame_data = b""
sample_frame_size = 0
expected_frame_size = 0

fps, st, frame_cnt, count = (0, 0, 20, 0)
displays = 0
chunks = 0
num = 0
timestamp = ""

latency_list = [0]

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

# Function to receive data and manage frames
def receive_data():
    global frame_data, expected_frame_size, displays, fps, st, count, chunks, num, timestamp, latency_list
    while True:
        packet, ret = client_socket.recvfrom(BUFFER_SIZE)
        # Checking for ending-frame:
        if(packet.startswith(b'@')):
            print("Received All Video Frames")
            # Plotting Network Latency
            latency_list.pop(0)
            latency_list.pop(len(latency_list)-1)
            x =  [i for i in range(1, len(latency_list) + 1)]
            plt.figure(figsize=(20, 10))
            plt.scatter(x, latency_list)
            plt.xlabel('Frame Number')
            plt.ylabel('Latency (in milliseconds)')
            plt.savefig('plot.png')
            print("SAVED IMAGE")
            break

        # Checking for video_frame initial packet.
        if packet.startswith(b'|'):
            # Parse the timestamp from the frame info
            timestamp = (float)(packet[1:16].decode())
            idx = len(latency_list) - 1
            val = (int)((timestamp - latency_list[idx])*1000)
            # print("LATENCY:",val)
            latency_list[idx] = val
            latency_list.append(time.time())
            frame_size = int(packet[16:].decode())
            num = packet[:3].decode()
            expected_frame_size = frame_size
            frame_data = b""
            chunks = 0
            # print("Received frame at timestamp:", timestamp)
            continue
        else:
            data = base64.b64decode(packet)
            frame_data += data
            chunks += 1
        
        if len(frame_data) >= expected_frame_size:
            displays += 1
            # print("Time - ", timestamp, "Curr-Time ", str(time.time()),"Frame NUM - ", displays, " chunks - ", chunks, " expec_frame_size - ", expected_frame_size, " frame_data - ", len(frame_data))
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

# Create a thread for processing frames
# processing_thread = threading.Thread(target=process_frames)
# processing_thread.start()
process_frames()
receive_thread.join()
# processing_thread.join()

# while True:
#     key = cv2.waitKey(1)  # Update the display
#     if key == ord('q'):
#         break

# Close the client socket when done.
client_socket.close()
cv2.destroyAllWindows()
