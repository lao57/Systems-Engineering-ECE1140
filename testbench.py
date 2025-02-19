from PyQt6.QtWidgets import QTableWidgetItem

class TestBench:
    def __init__(self, ctc_office):
        self.ctc_office = ctc_office
        self.block_data = {}  # Stores block occupancy states

    def initialize_block_occupancy(self):

        self.block_data = {}  # Reset block occupancy storage

        for block in range(1, 77):  # Red Line blocks
            self.block_data[(block, "Red Line")] = "Unoccupied"
        for block in range(1, 142):  # Green Line blocks
            self.block_data[(block, "Green Line")] = "Unoccupied"

        self.update_block_occupancy_table()

    def update_block_occupancy_table(self):

        current_line = self.ctc_office.comboBlockOccupancy.currentText()
        block_count = 76 if "red" in current_line.lower() else 141

        for row in range(block_count):
            block_number = row + 1
            status = self.block_data.get((block_number, current_line), "Unoccupied")
            self.ctc_office.tableBlockOccupancy.setItem(row, 1, QTableWidgetItem(status))

    def set_block_occupied(self, block_number, train_line):
    
        self.block_data[(block_number, train_line)] = "Occupied"

    def set_block_unoccupied(self, block_number, train_line):

        self.block_data[(block_number, train_line)] = "Unoccupied"