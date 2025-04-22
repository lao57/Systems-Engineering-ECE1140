import sys, os, openpyxl
from PyQt6 import QtWidgets, QtGui, QtCore
try:
    # When run from main.py
    from track_model.track_model_backend import TrackModelBackend
except ImportError:
    # When run directly
    from track_model_backend import TrackModelBackend



class TrackMapViewer(QtWidgets.QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.setWindowTitle("Track Map Viewer")
        self.setGeometry(100, 100, 1400, 800)

        # Create central widget
        self.centralWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.centralWidget)
        self.mainLayout = QtWidgets.QVBoxLayout(self.centralWidget)

        # Top bar layout for controls
        self.topBar = QtWidgets.QHBoxLayout()

        # Load button
        self.load_button = QtWidgets.QPushButton("Load Layout", self)
        self.load_button.clicked.connect(self.load_layout)
        self.topBar.addWidget(self.load_button)

        # Add zoom controls
        self.zoomLabel = QtWidgets.QLabel("Zoom:")
        self.topBar.addWidget(self.zoomLabel)

        self.zoomSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.zoomSlider.setMinimum(10)
        self.zoomSlider.setMaximum(200)
        self.zoomSlider.setValue(100)
        self.zoomSlider.setTickInterval(10)
        self.zoomSlider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.zoomSlider.valueChanged.connect(self.update_zoom)
        self.topBar.addWidget(self.zoomSlider)

        self.zoomValue = QtWidgets.QLabel("100%")
        self.topBar.addWidget(self.zoomValue)

        self.zoomInButton = QtWidgets.QPushButton("+", self)
        self.zoomInButton.setFixedWidth(40)
        self.zoomInButton.clicked.connect(self.zoom_in)
        self.topBar.addWidget(self.zoomInButton)

        self.zoomOutButton = QtWidgets.QPushButton("-", self)
        self.zoomOutButton.setFixedWidth(40)
        self.zoomOutButton.clicked.connect(self.zoom_out)
        self.topBar.addWidget(self.zoomOutButton)

        self.fitButton = QtWidgets.QPushButton("Fit to View", self)
        self.fitButton.clicked.connect(self.fit_to_view)
        self.topBar.addWidget(self.fitButton)

        # Add layout to main layout
        self.mainLayout.addLayout(self.topBar)

        # Graphics View
        self.graphicsView = QtWidgets.QGraphicsView(self)
        self.graphicsView.setScene(QtWidgets.QGraphicsScene())
        self.graphicsView.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self.graphicsView.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.graphicsView.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.graphicsView.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.graphicsView.setInteractive(True)
        self.graphicsView.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.mainLayout.addWidget(self.graphicsView)

        # Set the layout background to differentiate from scene
        self.graphicsView.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(20, 20, 20)))
        self.backend=backend
        self.backend.addUI(self)

        # two layouts: Green and Red
        self.line_positions = {
            "Green": {
                0: (10, 0),
                63: (30, 1), 64: (30, 2), 65: (30, 3), 66: (30, 4), 67: (30, 5),
                68: (30, 6), 69: (30, 7), 70: (30, 8), 71: (30, 9), 72: (29, 10), 73: (28, 11),
                74: (27, 11), 75: (26, 11), 76: (25, 11), 77: (24, 11), 78: (23, 11),
                79: (22, 11), 80: (21, 11), 81: (20, 11), 82: (19, 11), 83: (18, 11),
                84: (17, 11), 85: (16, 11), 86: (15, 11), 87: (14, 11), 88: (13, 11),
                89: (12, 10), 90: (11, 9), 91: (11, 8), 92: (11, 7), 93: (11, 6),
                94: (12, 5), 95: (13, 5), 96: (14, 5), 97: (15, 6), 98: (16, 7),
                99: (16, 8), 100: (16, 9), 101: (24, 10), 102: (25, 9), 103: (26, 9),
                104: (27, 9), 105: (28, 8), 106: (28, 7), 107: (28, 6), 108: (28, 5),
                109: (28, 4), 110: (28, 3), 111: (28, 2), 112: (28, 1), 113: (28, 0),
                114: (28, -1), 115: (28, -2), 116: (28, -3), 117: (28, -4), 118: (28, -5),
                119: (28, -6), 120: (27, -7), 121: (26, -8), 122: (25, -9), 123: (24, -9),
                124: (23, -9), 125: (22, -9), 126: (21, -9), 127: (20, -9), 128: (19, -9),
                129: (18, -9), 130: (17, -9), 131: (16, -9), 132: (15, -9), 133: (14, -9),
                134: (13, -9), 135: (12, -9), 136: (11, -9), 137: (10, -9), 138: (9, -9),
                139: (8, -9), 140: (7, -9), 141: (6, -9), 142: (5, -9), 143: (4, -9),
                144: (3, -10), 145: (2, -11), 146: (1, -12), 147: (1, -13), 148: (1, -14),
                149: (1, -15), 150: (2, -16), 29: (3, -15), 30: (3, -14),
                31: (3, -13), 32: (3, -12), 33: (4, -11), 34: (5, -11), 35: (6, -11),
                36: (7, -11), 37: (8, -11), 38: (9, -11), 39: (10, -11), 40: (11, -11),
                41: (12, -11), 42: (13, -11), 43: (14, -11), 44: (15, -11), 45: (16, -11),
                46: (17, -11), 47: (18, -11), 48: (19, -11), 49: (20, -11), 50: (21, -11),
                51: (22, -11), 52: (23, -11), 53: (24, -11), 54: (25, -11), 55: (26, -11),
                56: (27, -10), 58: (28, -9), 59: (29, -8), 60: (30, -7), 61: (30, -6),
                62: (30, -5),
                28: (3, -16), 27: (3, -17), 26: (3, -18), 25: (3, -19), 24: (3, -20), 23: (3, -21), 22: (3, -22),
                21: (3, -23),
                20: (3, -24), 19: (4, -25), 18: (5, -26), 17: (6, -26), 16: (7, -26), 15: (8, -26), 14: (9, -26),
                13: (10, -26), 12: (11, -26), 11: (12, -26), 10:(13,-26), 9: (14, -25), 8: (15, -24), 7: (15, -23),
                6:(15, -22), 5:(14,-22), 4:(13,-22), 3:(12,-23),2:(11,-24), 1:(11,-25),
            },
            "Red": {





            }
        }
        # start with Green
        self.custom_positions = self.line_positions["Green"]

        # Setup mouse wheel zooming
        self.graphicsView.wheelEvent = self.wheel_zoom
        QtCore.QTimer.singleShot(0, self.load_layout)

    def wheel_zoom(self, event):
        """Custom wheel event for zooming"""
        zoomFactor = 1.1 if event.angleDelta().y() > 0 else 0.9
        current_zoom = self.zoomSlider.value()
        new_zoom = int(current_zoom * zoomFactor)
        self.zoomSlider.setValue(max(min(new_zoom, 200), 10))

    def update_zoom(self, value):
        """Update zoom level from slider value"""
        scale_factor = value / 100.0
        self.zoomValue.setText(f"{value}%")
        current_center = self.graphicsView.mapToScene(self.graphicsView.viewport().rect().center())
        self.graphicsView.resetTransform()
        self.graphicsView.scale(scale_factor, scale_factor)
        self.graphicsView.centerOn(current_center)

    def zoom_in(self):
        """Zoom in button handler"""
        current_zoom = self.zoomSlider.value()
        self.zoomSlider.setValue(min(current_zoom + 10, 200))

    def zoom_out(self):
        """Zoom out button handler"""
        current_zoom = self.zoomSlider.value()
        self.zoomSlider.setValue(max(current_zoom - 10, 10))

    def fit_to_view(self):
        """Fit the entire layout to the view and center it"""
        if not self.graphicsView.scene().items():
            return
        self.graphicsView.resetTransform()
        rect = self.graphicsView.scene().itemsBoundingRect()
        margin = 50
        self.graphicsView.scene().setSceneRect(
            rect.x() - margin,
            rect.y() - margin,
            rect.width() + 2 * margin,
            rect.height() + 2 * margin
        )
        self.graphicsView.fitInView(self.graphicsView.scene().sceneRect(),
                                    QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        scale_factor = self.graphicsView.transform().m11() * 100
        self.zoomSlider.blockSignals(True)
        self.zoomSlider.setValue(min(max(int(scale_factor), 10), 200))
        self.zoomSlider.blockSignals(False)
        self.zoomValue.setText(f"{self.zoomSlider.value()}%")

    def load_layout(self):
        file_filter = 'Excel File (*.xlsx)'
        response, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Select Track Layout File',
            directory=os.getcwd(),
            filter=file_filter
        )
        if not response:
            return

        try:
            wb = openpyxl.load_workbook(response, data_only=True)
            sheet = wb.active
            self.last_sheet = sheet
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to read Excel file: {e}")
            return

        # pick mapping by sheet name (e.g. "Red ..." vs "Green ...")
        title = sheet.title.lower()
        if "red" in title:
            self.custom_positions = self.line_positions["Red"]
        else:
            self.custom_positions = self.line_positions["Green"]

        QtCore.QTimer.singleShot(100, lambda: self.draw_green_line(sheet, skip_fit=False))

    def draw_green_line(self, sheet, skip_fit=False):
        def parse_switch_connections(infra_text):
            import re
            connections = []
            matches = re.findall(r"SWITCH.*?\((.*?)\)", infra_text.upper())
            for group in matches:
                parts = group.split(";")
                for part in parts:
                    nums = [int(s.strip()) for s in part.split("-") if s.strip().isdigit()]
                    if len(nums) == 2:
                        connections.append((nums[0], nums[1]))
            return connections

        self.graphicsView.scene().clear()

        # Find the grid dimensions to calculate center offset
        min_x = min(pos[0] for pos in self.custom_positions.values())
        max_x = max(pos[0] for pos in self.custom_positions.values())
        min_y = min(pos[1] for pos in self.custom_positions.values())
        max_y = max(pos[1] for pos in self.custom_positions.values())

        # Calculate center of grid
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Calculate offset to center the layout
        block_size = 30
        spacing = 45
        offset_x = -center_x * spacing
        offset_y = -center_y * spacing

        block_positions = {}
        switch_lines = []

        for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True)):
            try:
                block_number = row[2]
                infra = str(row[6]).upper() if row[6] else ""
                if block_number is None or block_number not in self.custom_positions:
                    continue

                grid_x, grid_y = self.custom_positions[block_number]
                x = grid_x * spacing + offset_x
                y = grid_y * spacing + offset_y

                if self.backend.get_occupancy_status(block_number - 1):
                    color = QtGui.QColor(255, 0, 0)  # Red if occupied
                else:
                    if "STATION" in infra:
                        color = QtGui.QColor(0, 0, 255)  # Blue
                    elif "SWITCH" in infra:
                        color = QtGui.QColor(255, 165, 0)  # Orange
                    elif "RAILWAY CROSSING" in infra:
                        color = QtGui.QColor(128, 128, 128)  # Gray
                    elif "UNDERGROUND" in infra:
                        color = QtGui.QColor(128, 0, 128)  # Purple
                    else:
                        color = QtGui.QColor(0, 128, 0)  # Default green

                rect = QtWidgets.QGraphicsRectItem(x, y, block_size, block_size)
                rect.setBrush(color)
                rect.setToolTip(f"Block {block_number}: {infra}")
                self.graphicsView.scene().addItem(rect)

                label = QtWidgets.QGraphicsTextItem(str(block_number))
                label.setPos(x + 5, y + 5)
                label.setDefaultTextColor(QtGui.QColor(255, 255, 255))
                self.graphicsView.scene().addItem(label)

                if infra:
                    text = QtWidgets.QGraphicsTextItem(infra.split(';')[0][:7])
                    text.setPos(x, y + block_size + 2)
                    text.setScale(0.7)
                    text.setDefaultTextColor(QtGui.QColor(220, 220, 220))
                    self.graphicsView.scene().addItem(text)

                cx, cy = x + block_size/2, y + block_size/2
                block_positions[block_number] = (cx, cy)
                if "SWITCH" in infra:
                    switch_lines.extend(parse_switch_connections(infra))

            except Exception as e:
                print(f"Skipping row {i + 2} due to error: {e}")
                continue

        for from_block, to_block in switch_lines:
            if from_block in block_positions and to_block in block_positions:
                fx, fy = block_positions[from_block]
                tx, ty = block_positions[to_block]
                line = QtWidgets.QGraphicsLineItem(fx, fy, tx, ty)
                pen = QtGui.QPen(QtGui.QColor("orange"))
                pen.setWidth(2)
                pen.setStyle(QtCore.Qt.PenStyle.DashLine)
                line.setPen(pen)
                self.graphicsView.scene().addItem(line)

        # After drawing everything, fit to the layout
        if not skip_fit:
            self.fit_to_view()

    def resizeEvent(self, event):
        """Handle window resize events"""
        super().resizeEvent(event)
        if self.graphicsView.scene().items():
            self.fit_to_view()

    def update(self):
        if hasattr(self, 'last_sheet'):
            self.draw_green_line(self.last_sheet, skip_fit=True)


if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication(sys.argv)
        viewer = TrackMapViewer()
        viewer.show()
        ## to run map by itself
        #backend = TrackModelBackend()  # ✅ Instantiate backend
        #viewer = TrackMapViewer(backend)  # ✅ Pass backend to the viewer
        #viewer.show()
        ##
        sys.exit(app.exec())
    except Exception as e:
        print("Fatal Exception:", e)
        import traceback
        traceback.print_exc()
