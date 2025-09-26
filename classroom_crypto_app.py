# classroom_coin.py
import hashlib
import time
import json
from dataclasses import dataclass, asdict
from typing import List, Dict


# ---------- Transaction and Block ----------
@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: int
    note: str = ""

    def to_dict(self):
        return asdict(self)


class Block:
    def __init__(self, index: int, transactions: List[Transaction],
                 previous_hash: str, nonce: int = 0, timestamp: float = None):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.timestamp = timestamp or time.time()
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        tx_str = json.dumps([t.to_dict() for t in self.transactions], sort_keys=True)
        block_str = f"{self.index}{tx_str}{self.previous_hash}{self.nonce}{self.timestamp}".encode()
        return hashlib.sha256(block_str).hexdigest()


# ---------- Blockchain ----------
class SimpleBlockchain:
    def __init__(self, difficulty: int = 2):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block(index=0, transactions=[], previous_hash="0")
        self.chain.append(genesis)

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block: Block) -> Block:
        target = "0" * self.difficulty
        while not block.hash.startswith(target):
            block.nonce += 1
            block.hash = block.compute_hash()
        return block

    def add_block(self, transactions: List[Transaction]) -> Block:
        new_block = Block(len(self.chain), transactions, self.last_block.hash)
        mined = self.proof_of_work(new_block)
        self.chain.append(mined)
        return mined

    def get_balance(self, address: str) -> int:
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        return balance

    def all_balances(self) -> Dict[str, int]:
        balances: Dict[str, int] = {}
        for block in self.chain:
            for tx in block.transactions:
                balances[tx.sender] = balances.get(tx.sender, 0) - tx.amount
                balances[tx.recipient] = balances.get(tx.recipient, 0) + tx.amount
        return balances

    def print_ledger(self):
        for block in self.chain:
            print(f"Block #{block.index} | prev={block.previous_hash[:8]}... | hash={block.hash[:8]}... | nonce={block.nonce}")
            for tx in block.transactions:
                print(f"   {tx['sender'] if isinstance(tx, dict) else tx.sender} -> "
                      f"{tx['recipient'] if isinstance(tx, dict) else tx.recipient} : "
                      f"{tx['amount'] if isinstance(tx, dict) else tx.amount}  "
                      f"({tx['note'] if isinstance(tx, dict) else tx.note})")
            print()


# ---------- Classroom Coin ----------
TEACHER = "TEACHER"

class ClassroomCoin:
    def __init__(self, students: List[str], difficulty: int = 2):
        self.blockchain = SimpleBlockchain(difficulty)
        self.students = set(students)

    def award_coin(self, student: str, reason="Correct Answer"):
        if student not in self.students:
            raise ValueError(f"{student} is not a registered student.")
        tx = Transaction(sender=TEACHER, recipient=student, amount=1, note=reason)
        block = self.blockchain.add_block([tx])
        print(f"Mined block #{block.index}: Awarded 1 coin to {student} ({reason})")

    def transfer(self, sender: str, recipient: str, amount=1, note=""):
        if self.blockchain.get_balance(sender) < amount:
            raise ValueError(f"{sender} does not have enough balance.")
        tx = Transaction(sender=sender, recipient=recipient, amount=amount, note=note)
        block = self.blockchain.add_block([tx])
        print(f"Block #{block.index}: {sender} -> {recipient} : {amount} coin(s)")

    def balance(self, student: str) -> int:
        return self.blockchain.get_balance(student)

    def leaderboard(self):
        balances = self.blockchain.all_balances()
        sorted_balances = sorted(balances.items(), key=lambda x: x[1], reverse=True)
        print("\n=== Leaderboard ===")
        for rank, (student, bal) in enumerate(sorted_balances, start=1):
            print(f"{rank}. {student}: {bal} coins")
        print()


# ---------- Demo ----------
if __name__ == "__main__":
    students = ["Alice", "Bob", "Charlie", "Dee"]
    classroom = ClassroomCoin(students)

    print("=== Teacher awards coins ===")
    classroom.award_coin("Alice", "Q1 Correct")
    classroom.award_coin("Bob", "Q1 Correct")
    classroom.award_coin("Charlie", "Q1 Correct")
    classroom.award_coin("Alice", "Q2 Correct")
    classroom.award_coin("Bob", "Group Work Help")

    print("\n=== Balances ===")
    for s in students:
        print(f"{s}: {classroom.balance(s)}")

    print("\n=== Transfers ===")
    classroom.transfer("Alice", "Dee", 1, "Helping out")
    classroom.transfer("Bob", "Charlie", 1, "Thanks for notes")

    print("\n=== Final Balances ===")
    for s in students:
        print(f"{s}: {classroom.balance(s)}")

    classroom.leaderboard()

    print("=== Ledger ===")
    classroom.blockchain.print_ledger()