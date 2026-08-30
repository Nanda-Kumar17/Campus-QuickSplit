import ssl
import sqlite3
from datetime import datetime

# Bypass SSL certificate verification for initial binary setup downloads
ssl._create_default_https_context = ssl._create_unverified_context

import flet as ft

DB_NAME = "quicksplit.db"


# ==========================================
# 1. DATABASE LAYER (SQLITE LOCAL PERSISTENCE)
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table for Group Participants
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # Table for Expenses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            payer TEXT NOT NULL,
            split_among TEXT NOT NULL,
            split_amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


def get_participants_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM participants")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def add_participant_db(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO participants (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()


def remove_participant_db(name: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM participants WHERE name = ?", (name,))
    conn.commit()
    conn.close()


def save_expense_db(description, amount, payer, split_among_str, split_amount, timestamp):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (description, amount, payer, split_among, split_amount, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (description, amount, payer, split_among_str, split_amount, timestamp))
    conn.commit()
    conn.close()


def load_expenses_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, amount, payer, split_among, split_amount, timestamp FROM expenses ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    expenses = []
    for row in rows:
        expenses.append({
            "id": row[0],
            "description": row[1],
            "amount": row[2],
            "payer": row[3],
            "split_among": row[4].split(", "),
            "split_amount": row[5],
            "timestamp": row[6],
        })
    return expenses


# ==========================================
# 2. BUSINESS LOGIC & STATE MANAGEMENT
# ==========================================
class ExpenseManager:

    def __init__(self):
        init_db()
        self.participants = get_participants_db()
        self.expenses = load_expenses_db()

    def add_member(self, name: str) -> tuple[bool, str]:
        cleaned_name = name.strip()
        if not cleaned_name:
            return False, "Member name cannot be empty."
        if cleaned_name in self.participants:
            return False, "Member already exists."

        add_participant_db(cleaned_name)
        self.participants = get_participants_db()
        return True, f"Added {cleaned_name}!"

    def remove_member(self, name: str) -> tuple[bool, str]:
        if name not in self.participants:
            return False, "Member not found."

        remove_participant_db(name)
        self.participants = get_participants_db()
        return True, f"Removed {name}!"

    def add_expense(
        self, description: str, amount: float, payer: str, split_among: list
    ) -> tuple[bool, str]:
        if not description or not description.strip():
            return False, "Description cannot be empty."

        if amount <= 0:
            return False, "Amount must be greater than zero."

        if not payer or payer not in self.participants:
            return False, "Please select a valid payer."

        if not split_among:
            return False, "Select at least one participant to split with."

        split_amount = round(amount / len(split_among), 2)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        save_expense_db(
            description.strip(),
            amount,
            payer,
            ", ".join(split_among),
            split_amount,
            now_str,
        )

        self.expenses = load_expenses_db()
        return True, "Expense added successfully!"

    def calculate_balances(self):
        # 1. Collect active members along with anyone referenced in past expenses
        all_people = set(self.participants)
        for exp in self.expenses:
            all_people.add(exp["payer"])
            all_people.update(exp["split_among"])

        # 2. Initialize net balances for all involved individuals
        balances = {person: 0.0 for person in all_people}
        total_group_spending = 0.0

        # 3. Process expense calculations
        for exp in self.expenses:
            amount = exp["amount"]
            payer = exp["payer"]
            split_among = exp["split_among"]
            split_amount = exp["split_amount"]

            total_group_spending += amount

            # Credit the payer
            balances[payer] += amount

            # Debit each participant
            for person in split_among:
                balances[person] -= split_amount

        return balances, round(total_group_spending, 2)


# ==========================================
# 3. UI APPLICATION (FLET FRAMEWORK)
# ==========================================
def main(page: ft.Page):
    page.title = "Campus QuickSplit"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20

    manager = ExpenseManager()

    # Form State Controls
    desc_input = ft.TextField(
        label="Description (e.g., Daily Auto Ride)", expand=True
    )
    amount_input = ft.TextField(
        label="Amount (₹)", keyboard_type=ft.KeyboardType.NUMBER, width=150
    )
    payer_dropdown = ft.Dropdown(
        label="Paid By",
        options=[ft.dropdown.Option(p) for p in manager.participants],
        width=180,
    )

    checkboxes = {
        p: ft.Checkbox(label=p, value=True) for p in manager.participants
    }
    split_checkbox_group = ft.Row(
        controls=list(checkboxes.values()), wrap=True
    )

    new_member_input = ft.TextField(
        label="Custom Member Name", width=220
    )

    member_chips_row = ft.Row(wrap=True)

    error_banner = ft.Text(color=ft.Colors.RED_600, visible=False, weight=ft.FontWeight.BOLD)
    total_spending_text = ft.Text("Total Spending: ₹0.00", size=18, weight=ft.FontWeight.BOLD)
    balances_container = ft.Column()
    activity_log_container = ft.Column()

    def refresh_member_ui():
        payer_dropdown.options = [
            ft.dropdown.Option(p) for p in manager.participants
        ]

        split_checkbox_group.controls.clear()
        checkboxes.clear()
        for p in manager.participants:
            cb = ft.Checkbox(label=p, value=True)
            checkboxes[p] = cb
            split_checkbox_group.controls.append(cb)

        member_chips_row.controls.clear()
        for p in manager.participants:
            member_chips_row.controls.append(
                ft.Chip(
                    label=ft.Text(p),
                    on_delete=lambda e, name=p: handle_remove_member(name),
                )
            )

    def handle_add_member(e):
        error_banner.visible = False
        success, msg = manager.add_member(new_member_input.value)
        if success:
            new_member_input.value = ""
            refresh_member_ui()
            update_dashboard()
        else:
            error_banner.value = msg
            error_banner.visible = True
            page.update()

    def handle_remove_member(name):
        error_banner.visible = False
        success, msg = manager.remove_member(name)
        if success:
            refresh_member_ui()
            update_dashboard()
        else:
            error_banner.value = msg
            error_banner.visible = True
            page.update()

    def update_dashboard():
        balances, total_spending = manager.calculate_balances()

        total_spending_text.value = f"Total Group Spending: ₹{total_spending:.2f}"

        balances_container.controls.clear()
        for participant, net_bal in balances.items():
            if net_bal > 0:
                bal_color = ft.Colors.GREEN_600
                status_text = f"gets back ₹{net_bal:.2f}"
            elif net_bal < 0:
                bal_color = ft.Colors.RED_600
                status_text = f"owes ₹{abs(net_bal):.2f}"
            else:
                bal_color = ft.Colors.GREY_600
                status_text = "is settled up"

            balances_container.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(participant, weight=ft.FontWeight.BOLD, size=16),
                            ft.Text(status_text, color=bal_color, weight=ft.FontWeight.W_500),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=8,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=6,
                )
            )

        activity_log_container.controls.clear()
        if not manager.expenses:
            activity_log_container.controls.append(
                ft.Text("No expenses logged yet.", italic=True, color=ft.Colors.GREY_500)
            )
        else:
            for exp in manager.expenses:
                activity_log_container.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.BLUE_600),
                                        title=ft.Text(f"{exp['description']} — ₹{exp['amount']:.2f}"),
                                        subtitle=ft.Text(
                                            f"Paid by {exp['payer']} • Split among: {', '.join(exp['split_among'])}\n{exp['timestamp']}"
                                        ),
                                    ),
                                ]
                            ),
                            padding=5,
                        )
                    )
                )

        page.update()

    def handle_add_expense(e):
        error_banner.visible = False

        desc = desc_input.value
        try:
            amt = float(amount_input.value) if amount_input.value else 0.0
        except ValueError:
            error_banner.value = "Please enter a valid numeric amount."
            error_banner.visible = True
            page.update()
            return

        payer = payer_dropdown.value
        selected_split = [
            p for p, cb in checkboxes.items() if cb.value
        ]

        success, message = manager.add_expense(desc, amt, payer, selected_split)

        if not success:
            error_banner.value = message
            error_banner.visible = True
        else:
            desc_input.value = ""
            amount_input.value = ""
            payer_dropdown.value = None
            for cb in checkboxes.values():
                cb.value = True

            update_dashboard()

        page.update()

    # Dynamic Member Management Layout Card
    member_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Manage Group Members", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            new_member_input,
                            ft.ElevatedButton(
                                "Add Member",
                                icon=ft.Icons.PERSON_ADD,
                                on_click=handle_add_member,
                            ),
                        ]
                    ),
                    ft.Text("Current Members (Click 'X' to remove):", weight=ft.FontWeight.W_500),
                    member_chips_row,
                ],
                spacing=10,
            ),
            padding=15,
        )
    )

    # Expense Entry Form Card
    form_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Log New Expense", size=18, weight=ft.FontWeight.BOLD),
                    error_banner,
                    ft.Row([desc_input, amount_input]),
                    ft.Row([payer_dropdown]),
                    ft.Text("Split Equally Among:", weight=ft.FontWeight.W_500),
                    split_checkbox_group,
                    ft.ElevatedButton(
                        "Add Expense",
                        icon=ft.Icons.ADD,
                        on_click=handle_add_expense,
                        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_600),
                    ),
                ],
                spacing=12,
            ),
            padding=15,
        )
    )

    page.add(
        ft.Text("Campus QuickSplit", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
        member_card,
        form_card,
        ft.Divider(),
        total_spending_text,
        ft.Text("Aggregated Net Balances", size=18, weight=ft.FontWeight.BOLD),
        balances_container,
        ft.Divider(),
        ft.Text("Activity Log", size=18, weight=ft.FontWeight.BOLD),
        activity_log_container,
    )

    refresh_member_ui()
    update_dashboard()


if __name__ == "__main__":
    ft.run(main)
