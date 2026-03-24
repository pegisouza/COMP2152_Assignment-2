import socket
import threading
import sqlite3
import os
import platform
import datetime

print(f"Python version: {platform.python_version()}")
print(f"OS name: {os.name}")

"""
Author: <Pedro Souza>
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime

# TODO: Print Python version and OS name (Step iii)

# TODO: Create the common_ports dictionary (Step iv)
# Add a 1-line comment above it explaining what it stores
# dictionary stores maps port numbers to their corresponding service names

common_ports = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}


# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"

class NetworkTool:
    
    def __init__(self, target):
        self.__target = target  # private property

    # Using @property and @target.setter allows us to control how the private attribute is accessed and modified.
    # Instead of accessing it directly, we can add validation rules, such as preventing an empty target value.
    # This helps protect the internal state of the object and avoids invalid data, resulting a safer and more organized code, and easier to maintain.   
    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, value):
        if value == "":
            print("Error: Target cannot be empty")
        else:
            self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")


# Q3: What is the benefit of using @property and @target.setter?
# TODO: Your 2-4 sentence answer here... (Part 2, Q3)

# Q1: How does PortScanner reuse code from NetworkTool?
# TODO: Your 2-4 sentence answer here... (Part 2, Q1)
# PortScanner reuses code from NetworkTool by inheriting from it.
# For example, it uses super().__init__(target) to set the target without writing the same code again.
# It can also use the getter and setter from the parent class. This makes the code simpler and avoids repetition.



# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)
# - Constructor: call super().__init__(target), initialize self.scan_results = [], self.lock = threading.Lock()
# - Destructor: print "PortScanner instance destroyed", call super().__del__()#
# - scan_port(self, port):
class PortScanner(NetworkTool):
    def __init__(self, target):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock()

    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()  


# Q4: What would happen without try-except here?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q4)
#     Without try-except, the program could crash if a socket error happens while scanning a port.
#     If the machine is not reachable, the error could stop the whole scan. 
#     For this reason, using try-except helps the program continue running and show an error message instead.


#     - try-except with socket operations
#     - Create socket, set timeout, connect_ex
#     - Determine Open/Closed status
#     - Look up service name from common_ports (use "Unknown" if not found)
#     - Acquire lock, append (port, status, service_name) tuple, release lock
#     - Close socket in finally block
#     - Catch socket.error, print error message#
#     - get_open_ports(self):
#     - Use list comprehension to return only "Open" results
    
    def scan_port(self, port):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)

            result = sock.connect_ex((self.target, port))

            if result == 0:
                status = "Open"
            else:
                status = "Closed"

            service_name = common_ports.get(port, "Unknown")

            self.lock.acquire()
            self.scan_results.append((port, status, service_name))
            self.lock.release()

        except socket.error as e:
            print(f"Error scanning port {port}: {e}")

        finally:
            if sock:
                sock.close()


#
#     Q2: Why do we use threading instead of scanning one port at a time?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q2)
#     We use threading to scan many ports at the same time, which makes the program faster.
#     If the program scanned one port at a time, it would take much longer, especially for a large range of ports (e.g. 1024 ports sequentially).
#     This is useful because each port scan may wait for a response before moving to the next one.


#     - scan_range(self, start_port, end_port):
#     - Create threads list
#     - Create Thread for each port targeting scan_port
#     - Start all threads (one loop)
#     - Join all threads (separate loop)

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

    def scan_range(self, start_port, end_port):
        threads = []

        for port in range(start_port, end_port + 1):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()


# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error

def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            port INTEGER,
            status TEXT,
            service TEXT,
            scan_date TEXT
        )
        """)

        for port, status, service in results:
            cursor.execute("""
            INSERT INTO scans (target, port, status, service, scan_date)
            VALUES (?, ?, ?, ?, ?)
            """, (target, port, status, service, str(datetime.datetime.now())))

        conn.commit()
        conn.close()

    except sqlite3.Error as e:
        print("Database error:", e)


# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection

def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()

        for row in rows:
            print(f"[{row[5]}] {row[1]} : Port {row[2]} ({row[4]}) - {row[3]}")

        conn.close()

    except sqlite3.Error:
        print("No past scans found.")


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    pass
    # TODO: Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."

if __name__ == "__main__":
    target = input("Enter target IP address (press Enter for 127.0.0.1): ").strip()
    if target == "":
        target = "127.0.0.1"

    while True:
        try:
            start_port = int(input("Enter start port (1-1024): "))
            if start_port < 1 or start_port > 1024:
                print("Port must be between 1 and 1024.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    while True:
        try:
            end_port = int(input("Enter end port (1-1024): "))
            if end_port < 1 or end_port > 1024:
                print("Port must be between 1 and 1024.")
                continue
            if end_port < start_port:
                print("End port must be greater than or equal to start port.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")





    # TODO: After valid input (Step x)
    # - Create PortScanner object
    # - Print "Scanning {target} from port {start} to {end}..."
    # - Call scan_range()
    # - Call get_open_ports() and print results
    # - Print total open ports found
    # - Call save_results()
    # - Ask "Would you like to see past scan history? (yes/no): "
    # - If "yes", call load_past_scans()

    scanner = PortScanner(target)
    print(f"Scanning {target} from port {start_port} to {end_port}...")

    scanner.scan_range(start_port, end_port)

    open_ports = scanner.get_open_ports()

    print(f"--- Scan Results for {target} ---")
    for port, status, service in open_ports:
        print(f"Port {port}: {status} ({service})")
    print("------")
    print(f"Total open ports found: {len(open_ports)}")

    save_results(target, scanner.scan_results)

    history_choice = input("Would you like to see past scan history? (yes/no): ").strip().lower()
    if history_choice == "yes":
        load_past_scans()


# Q5: New Feature Proposal
# TODO: Your 2-3 sentence description here... (Part 2, Q5)
# Diagram: See diagram_101530025.png in the repository root
# One feature I would add is a filter that shows only ports for a specific service, such as HTTP or SSH.
# This would make the scan results easier to read, especially when many ports are found.
# It could be implemented using a list comprehension to return only the results that match the selected service name.
