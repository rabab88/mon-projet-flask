import os
import qrcode
import uuid
import hashlib
import json
from datetime import datetime

def generate_user_id():
    return str(uuid.uuid4())

def generate_qr_code(user_id):
    qr_code_dir = 'static/qr_codes'
    if not os.path.exists(qr_code_dir):
        os.makedirs(qr_code_dir)
    img = qrcode.make(user_id)
    file_path = os.path.join(qr_code_dir, f"{user_id}.png")
    img.save(file_path)
    return file_path

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def mine_block(self, difficulty):
        target = '0' * difficulty
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

class Blockchain:
    def __init__(self, difficulty=4):  
        self.chain = []
        self.difficulty = difficulty
        self.data_dir = 'data'
        self.blockchain_file = os.path.join(self.data_dir, 'blockchain.json')

        if os.path.exists(self.blockchain_file):
            self.load_blockchain()
            print("Loaded existing blockchain")
        else:
            self.create_genesis_block()
            print("Created genesis block")

    def create_genesis_block(self):
        genesis_block = Block(0, datetime.now().isoformat(), {'message': 'Genesis Block'}, '0')
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        self.save_blockchain()

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, data):
        previous_block = self.get_latest_block()
        new_block = Block(
            previous_block.index + 1,
            datetime.now().isoformat(),
            data,
            previous_block.hash
        )
        print(f"⛏️ Mining block {new_block.index}...")
        new_block.mine_block(self.difficulty)
        print(f"Block {new_block.index} mined: {new_block.hash}")
        self.chain.append(new_block)
        self.save_blockchain()

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                return False
            if current_block.previous_hash != previous_block.hash:
                return False
        return True

    def save_blockchain(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        with open(self.blockchain_file, 'w') as f:
            json.dump([{
                'index': block.index,
                'timestamp': block.timestamp,
                'data': block.data,
                'previous_hash': block.previous_hash,
                'nonce': block.nonce,
                'hash': block.hash
            } for block in self.chain], f, indent=2)

    def load_blockchain(self):
        with open(self.blockchain_file, 'r') as f:
            blocks = json.load(f)
            self.chain = []
            for block_data in blocks:
                block = Block(
                    block_data['index'],
                    block_data['timestamp'],
                    block_data['data'],
                    block_data['previous_hash']
                )
                block.nonce = block_data.get('nonce', 0)
                block.hash = block_data['hash']
                self.chain.append(block)

class SmartContract:
    def validate_registration(self, user_data, blockchain):
        for block in blockchain.chain:
            if block.data.get('type') == 'registration' and block.data.get('national_id') == user_data['national_id']:
                return False, "National ID already exists"
        if not (user_data['phone'].isdigit() and len(user_data['phone']) == 10):
            return False, "Invalid phone number"
        try:
            birth_date = datetime.strptime(user_data['birth_date'], '%Y-%m-%d')
            if birth_date >= datetime.now():
                return False, "Birth date must be in the past"
        except ValueError:
            return False, "Invalid birth date format"
        return True, "Valid"

    def validate_lab_submission(self, submission_data, blockchain):
        lab_user_id = submission_data.get('lab_user_id')
        lab_id = submission_data.get('lab_id')
        lab_exists = False
        patient_exists = False
        for block in blockchain.chain:
            if block.data.get('type') == 'registration':
                if block.data.get('user_id') == lab_user_id and block.data.get('profession') == 'lab':
                    lab_exists = True
                if block.data.get('user_id') == lab_id and block.data.get('profession') == 'lab':
                    patient_exists = True
        if not lab_exists:
            return False, "Submitter is not a valid Lab Technician"
        if not patient_exists:
            return False, "Patient ID does not exist"
        return True, "Valid"
