import sys
import socket
import threading
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QCheckBox, QSlider
from PyQt6.QtCore import Qt

class TestbenchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Testbench - Failure Injection & Temperature Control")
        self.setGeometry(200, 200, 400, 400)  # Adjusted for temperature control
        self.setStyleSheet("background-color: #2c3e50; color: white;")

        self.failures = {
            "Broken Rail": False,
            "Track Circuit": False,
            "Transponder": False,
            "Power Failure": False
        }
        self.temperature = 70  # Default temperature in °F

        self.initUI()
        self.start_server()

    def initUI(self):
        layout = QVBoxLayout()

        # Failure Selection Section
        self.status_label = QLabel("Select failures to inject:")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.checkboxes = {}
        for failure in self.failures:
            checkbox = QCheckBox(failure)
            checkbox.setStyleSheet("font-size: 12px; padding: 5px;")
            checkbox.stateChanged.connect(self.update_failures)
            layout.addWidget(checkbox)
            self.checkboxes[failure] = checkbox

        # Temperature Control Section
        self.temp_label = QLabel(f"Temperature: {self.temperature}°F")
        self.temp_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.temp_label)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setMinimum(-50)
        self.temp_slider.setMaximum(120)
        self.temp_slider.setValue(self.temperature)  # Default temp
        self.temp_slider.setStyleSheet("background-color: black;")
        self.temp_slider.valueChanged.connect(self.update_temperature)
        layout.addWidget(self.temp_slider)

        # Set layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_failures(self):
        """Update failure states based on checkbox selections"""
        for failure, checkbox in self.checkboxes.items():
            self.failures[failure] = checkbox.isChecked()

    def update_temperature(self):
        """Update temperature value from slider"""
        self.temperature = self.temp_slider.value()
        self.temp_label.setText(f"Temperature: {self.temperature}°F")

    def start_server(self):
        """Starts a socket server to send failure & temperature updates to Track Model UI"""
        def server():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow reuse of address
                s.bind(("localhost", 65432))  # Ensure port matches UI
                s.listen()

                print("Testbench server running... Waiting for UI connection.")

                while True:
                    conn, addr = s.accept()
                    with conn:
                        request = conn.recv(1024).decode()
                        if request == "Request Failures":
                            failures_active = [f for f, state in self.failures.items() if state]
                            response = f"Failure: {', '.join(failures_active)}" if failures_active else "No Failures"
                            response += f" | Temperature: {self.temperature}"  # Append temperature
                            conn.sendall(response.encode("utf-8"))

        thread = threading.Thread(target=server, daemon=True)
        thread.start()
