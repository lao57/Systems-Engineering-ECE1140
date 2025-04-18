import sys, os, openpyxl
from PyQt6 import QtWidgets, QtGui, QtCore


class TrackMapViewer(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Track Map Viewer (Safe Mode)")
        self.setGeometry(100, 100, 1400, 800)

        # Load button
        self.load_button = QtWidgets.QPushButton("Load Layout", self)
        self.load_button.setGeometry(50, 30, 150, 30)
        self.load_button.clicked.connect(self.load_layout)

        # Graphics View
        self.graphicsView = QtWidgets.QGraphicsView(self)
        self.graphicsView.setGeometry(50, 80, 1300, 680)
        self.graphicsView.setScene(QtWidgets.QGraphicsScene())
        self.graphicsView.setSceneRect(-500, -1000, 2500, 2000)

        # Updated custom layout from Green Line image
        self.custom_positions = {
            0: (10, 0),
            63: (30, 1), 64: (30, 2), 65: (30, 3), 66: (30, 4), 67: (30, 5),
            68: (30, 6), 69: (30, 7), 70: (30, 8), 71: (30, 9), 72: (29, 10), 73: (28, 11),

            # Right curve 74-78
            74: (27, 11), 75: (26, 11), 76: (25, 11), 77: (24, 11), 78: (23, 11), 79: (22, 11), 80: (21, 11),
            81: (20, 11), 82: (19, 11), 83: (18, 11), 84: (17, 11),

            # Left curve 85-100
            85: (16, 11), 86: (15, 11), 87: (14, 11), 88: (13, 11), 89: (12, 10),
            90: (11, 9), 91: (11, 8), 92: (11, 7), 93: (11, 6), 94: (12, 5),
            95: (13, 5), 96: (14, 5), 97: (15, 6), 98: (16, 7), 99: (16, 8), 100: (16, 9),

            101: (24, 10), 102: (25, 9), 103: (26, 9), 104: (27, 9), 105: (28, 8), 106: (28, 7), 107: (28, 6),
            108: (28, 5), 109: (28, 4), 110: (28, 3),
            111: (28, 2), 112: (28, 1), 113: (28, 0), 114: (28, -1), 115: (28, -2), 116: (28, -3), 117: (28, -4),
            118: (28, -5), 119: (28, -6),
            120: (27, -7), 121: (26, -8), 122: (25, -9), 123: (24, -9), 124: (23, -9), 125: (22, -9), 126: (21, -9),
            127: (20, -9),
            128: (19, -9), 129: (18, -9), 130: (17, -9), 131: (16, -9), 132: (15, -9), 133: (14, -9), 134: (13, -9),
            135: (12, -9), 136: (11, -9), 137: (10, -9), 138: (9, -9), 139: (8, -9), 140: (7, -9), 141: (6, -9),
            142: (5, -9), 143: (4, -9),
            144: (3, -10), 145: (2, -11), 146: (1, -12), 147: (1, -13), 148: (1, -14), 149: (1, -15), 150: (2, -16),

        }

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
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to read Excel file: {e}")
            return

        QtCore.QTimer.singleShot(100, lambda: self.draw_green_line(sheet))

    def draw_green_line(self, sheet):
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

        spacing = 45
        block_size = 30
        block_positions = {}
        switch_lines = []

        for i, row in enumerate(sheet.iter_rows(min_row=2, values_only=True)):
            try:
                block_number = row[2]
                infra = str(row[6]).upper() if row[6] else ""
                if block_number is None or block_number not in self.custom_positions:
                    continue

                grid_x, grid_y = self.custom_positions[block_number]
                x = 50 + grid_x * spacing
                y = 50 + grid_y * spacing

                color = QtGui.QColor(0, 128, 0)
                if "STATION" in infra:
                    color = QtGui.QColor(0, 0, 255)
                elif "SWITCH" in infra:
                    color = QtGui.QColor(255, 165, 0)
                elif "RAILWAY CROSSING" in infra:
                    color = QtGui.QColor(128, 128, 128)
                elif "UNDERGROUND" in infra:
                    color = QtGui.QColor(128, 0, 128)

                rect = QtWidgets.QGraphicsRectItem(x, y, block_size, block_size)
                rect.setBrush(color)
                rect.setToolTip(f"Block {block_number}: {infra}")
                self.graphicsView.scene().addItem(rect)

                label = QtWidgets.QGraphicsTextItem(str(block_number))
                label.setPos(x + 5, y + 5)
                self.graphicsView.scene().addItem(label)

                if infra:
                    text = QtWidgets.QGraphicsTextItem(infra.split(';')[0][:7])
                    text.setPos(x, y + block_size + 2)
                    text.setScale(0.7)
                    self.graphicsView.scene().addItem(text)

                center_x = x + block_size / 2
                center_y = y + block_size / 2
                block_positions[block_number] = (center_x, center_y)

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


if __name__ == "__main__":
    try:
        app = QtWidgets.QApplication(sys.argv)
        viewer = TrackMapViewer()
        viewer.show()
        sys.exit(app.exec())
    except Exception as e:
        print("Fatal Exception:", e)
        import traceback

        traceback.print_exc()
