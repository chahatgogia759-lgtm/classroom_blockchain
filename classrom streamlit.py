import streamlit as st
from typing import List, Dict
import pandas as pd

# import your classroom backend (make sure classroom_crypto_app.py is in same folder)
from classroom_crypto_app import ClassroomCoin, Transaction, TEACHER

st.set_page_config(page_title="Classroom Coin", layout="wide")

st.title("🎓 ClassroomCoin — Streamlit Interface")

# ---------- Helpers ----------
def ledger_to_rows(blockchain):
    rows = []
    for block in blockchain.chain:
        for tx in block.transactions:
            # Transaction objects have attributes sender, recipient, amount, note
            rows.append({
                "block_index": block.index,
                "timestamp": getattr(block, "timestamp", ""),
                "nonce": getattr(block, "nonce", ""),
                "prev_hash": str(block.previous_hash)[:12] + "...",
                "hash": str(block.hash)[:12] + "...",
                "sender": tx.sender,
                "recipient": tx.recipient,
                "amount": tx.amount,
                "note": tx.note,
            })
    return rows

def balances_table(classroom):
    balances = classroom.blockchain.all_balances()
    df = pd.DataFrame(list(balances.items()), columns=["student", "balance"])
    df = df.sort_values("balance", ascending=False).reset_index(drop=True)
    return df

# ---------- Session state init ----------
if "classroom" not in st.session_state:
    # default students (change as needed)
    default_students = ["Alice", "Bob", "Charlie", "Dee"]
    st.session_state.classroom = ClassroomCoin(default_students, difficulty=2)

classroom: ClassroomCoin = st.session_state.classroom

# ---------- Left column: Controls ----------
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Controls")

    # add student
    with st.form("add_student_form", clear_on_submit=True):
        new_student = st.text_input("Add student (name)")
        add_btn = st.form_submit_button("Add student")
        if add_btn and new_student:
            # rebuild ClassroomCoin with new student set (simple approach)
            students = list(classroom.students) + [new_student]
            st.session_state.classroom = ClassroomCoin(students, difficulty=classroom.blockchain.difficulty)
            st.success(f"Added student: {new_student}")

    # award coin (teacher -> student)
    st.subheader("Award coin (Teacher ▶ Student)")
    student_to_award = st.selectbox("Choose student", sorted(list(classroom.students)))
    award_reason = st.text_input("Reason", value="Correct Answer")
    if st.button("Award 1 coin"):
        try:
            classroom.award_coin(student_to_award, award_reason or "Award")
            st.success(f"Awarded 1 coin to {student_to_award}")
        except Exception as e:
            st.error(str(e))

    st.markdown("---")

    # transfer between students
    st.subheader("Transfer coins (Student ▶ Student)")
    students_sorted = sorted(list(classroom.students))
    col_a, col_b = st.columns(2)
    with col_a:
        sender = st.selectbox("Sender", students_sorted, index=0, key="sender")
    with col_b:
        recipient = st.selectbox("Recipient", students_sorted, index=1, key="recipient")
    amount = st.number_input("Amount", min_value=1, value=1, step=1)
    note = st.text_input("Note (optional)")
    if st.button("Transfer"):
        try:
            classroom.transfer(sender, recipient, amount, note)
            st.success(f"{sender} ➜ {recipient} : {amount} coin(s)")
        except Exception as e:
            st.error(str(e))

    st.markdown("---")
    if st.button("Recreate classroom (reset ledger)"):
        students = sorted(list(classroom.students))
        st.session_state.classroom = ClassroomCoin(students, difficulty=classroom.blockchain.difficulty)
        st.experimental_rerun()

# ---------- Right column: Displays ----------
with col2:
    st.header("Dashboard")

    # Balances
    st.subheader("Balances")
    df_bal = balances_table(classroom)
    if df_bal.empty:
        st.info("No transactions yet — balances are zero.")
    else:
        st.dataframe(df_bal, use_container_width=True)

    # Leaderboard
    st.subheader("Leaderboard")
    if df_bal.empty:
        st.write("No leaderboard yet.")
    else:
        st.table(df_bal.head(10).assign(rank=range(1, min(len(df_bal), 10)+1)).set_index("rank"))

    # Ledger
    st.subheader("Ledger (blocks & transactions)")
    ledger_rows = ledger_to_rows(classroom.blockchain)
    if ledger_rows:
        ledger_df = pd.DataFrame(ledger_rows)
        st.dataframe(ledger_df.sort_values(["block_index", "timestamp"], ascending=[True, True]), use_container_width=True)
    else:
        st.info("Ledger is empty.")

    # Quick actions / info
    st.markdown("---")
    st.subheader("Quick Info")
    st.write(f"Registered students: {', '.join(sorted(list(classroom.students)))}")
    st.write(f"Blockchain difficulty (proof-of-work zeroes): {classroom.blockchain.difficulty}")
    st.write(f"Blocks mined: {len(classroom.blockchain.chain)}")
