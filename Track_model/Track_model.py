class TrackModel:
    def __init__(self):
        self.blocks = {}  # Dictionary to store block information

    def add_block(self, block_number, beacon_signal="0000", grade=None, block_vector=None):
        self.blocks[block_number] = {
            'beacon_signal': beacon_signal,
            'grade': grade,
            'block_vector': block_vector,
            'baud_sig': None
        }

    def get_beacon_from_block(self, block_number):
        if block_number in self.blocks and self.blocks[block_number]['beacon_signal'] is not None:
            return self.blocks[block_number]['beacon_signal']
        return None

    def get_grade_from_block(self, block_number):
        if block_number in self.blocks and self.blocks[block_number]['grade'] is not None:
            return self.blocks[block_number]['grade']
        return None

    def get_block_vector_from_block(self, block_number):
        if block_number in self.blocks and self.blocks[block_number]['block_vector'] is not None:
            return self.blocks[block_number]['block_vector']
        return None
    
    def get_baud_sig(self, block_number):
        if block_number in self.blocks and self.blocks[block_number]['baud_sig'] is not None:
            return self.blocks[block_number]['baud_sig']
        return None
    
    def set_baud_sig(self, block_number, baud_sig):
        if block_number in self.blocks:
            self.blocks[block_number]['baud_sig'] = baud_sig

# Example usage:

if __name__ == '__main__':
    track_model = TrackModel()
    track_model.add_block(1, '1000000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010010110110110110110110110110110100000000000000000NONENONENONENONENONEStaBStaBStaBStaBStaB', [0,0,0,0,0,0,0,0,0,0], [1,2,3,4,5,6,7,8,9,10])
    track_model.add_block(2)
    track_model.add_block(3)
    track_model.add_block(4)
    track_model.add_block(5)
    track_model.add_block(6)
    track_model.add_block(7)
    track_model.add_block(8)
    track_model.add_block(9)
    track_model.add_block(10)

    track_model.set_baud_sig(1, '0000100000')

    beacon_signal = track_model.get_beacon_from_block(1)
    grade = track_model.get_grade_from_block(1)
    block_vector = track_model.get_block_vector_from_block(1)

    print(f"Beacon Signal: {beacon_signal}")
    print(f"Grade: {grade}")
    print(f"Block Vector: {block_vector}")

    # Testing block with only a block number
    beacon_signal_3 = track_model.get_beacon_from_block(3)
    grade_3 = track_model.get_grade_from_block(3)
    block_vector_3 = track_model.get_block_vector_from_block(3)

    print(f"Beacon Signal (Block 3): {beacon_signal_3}")
    print(f"Grade (Block 3): {grade_3}")
    print(f"Block Vector (Block 3): {block_vector_3}")





"""Blue line beacon

110010 = 50 meters
101 = 40 km/hr
1 = underground
0 = not at station


two blocks:
TID             Distance          Speed     Underground     At Station Station Name
0000     1101011101 0100110100 | 101 111 |      U V       |    S Z    | STA1 STA2
000011010111010100110100101111UVSZSTA1STA2

0000 0001100100 0001100100 0001100100 0001100100 0001100100 101 101 101 101 101 0000000000 NONE NONE NONE NONE NONE
LINE A:
0000000110010000011001000001100100000110010000011001001011011011011010000000000NONENONENONENONENONE
LINE AB:
0000000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010010110110110110110110110110110100000000000000000000NONENONENONENONENONEStaBStaBStaBStaBStaB
0,0,0,0,0,0,0,0,0,0
1,2,3,4,5,6,7,8,9,10
LINE AC:
0000000110010000011001000001100100000110010000011001000001100100000110010000011001000001100100000110010010110110110110110110110110110100000000000000000000NONENONENONENONENONEStaBStaBStaBStaBStaB
0,0,0,0,0,0,0,0,0,0
1,2,3,4,5,11,12,13,14,15





"""