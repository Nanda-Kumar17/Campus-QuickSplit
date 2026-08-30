**Campus QuickSplit App**

&#x20;  A lightweight, local-first, peer-to-peer group expense-tracking application designed for college students and groups. Campus QuickSplit eliminates the friction of cloud-based split apps by avoiding mandatory user signups, phone/email logins, internet dependencies, and slow cloud synchronization. 

&#x20;
**​Key Features**

* Local-First Persistence: Built-in SQLite database (sqlite3) stores all transactions and group member data locally on your device without network calls.
* Frictionless Onboarding: Zero login, authentication, or network setup required.  
* 
​Proportional Equal Distribution: Automatically calculates equal split amounts for selected group members based on total cost.  
* 
​Aggregated Net Balances: Live central dashboard tracking each member's overall standing (who owes money and who is owed money).
* &#x20; 
​Dynamic Member Management: Add or remove custom group members directly within the UI.
* &#x20; 
​Activity Log: Time-ordered transaction log displaying metadata, expense details, and timestamps.
* &#x20; 
​Input Sanitization: Front-end validation preventing blank fields, negative values, or empty split selections.  


**​Architecture \& Tech Stack**
​Language: Python 3.11 64bit
​UI Framework: Flet (Flutter-backed UI framework for Python)  
​Database: SQLite3 (Python native library)  


**​File Structure**

campus-quicksplit/

├── db support.py          # Database initialization, SQLite CRUD operations for members \& expenses

├── Front end UI.py         # Business logic (ExpenseManager) and Flet UI application

└── README.md      # Project documentation



**How It Works**

**​Math Logic**

​When an expense is logged, the total cost is divided equally among the checked participants:

Share per person= total expense amount/ number of selected participants



* ​Payer: Credited the full total amount paid.  
* ​Participants: Debited their calculated equal share.  
* ​Net Status:
1. ​Green: Member gets back money (net balance > 0).  
2. ​Red: Member owes money (net balance < 0).  
3. ​Grey: Member is settled up (net balance = 0).  



**​How to Use the App**

* ​Manage Members: Use the Manage Group Members card to add new custom names or remove members.  
* ​Log an Expense:
1. ​Enter a short Description (e.g., Daily Auto Ride, Coffee).  
2. ​Enter the Amount (₹).  
3. ​Select who Paid By from the dropdown menu.  
4. ​Check off the members included in Split Equally Among.  
5. ​Click Add Expense.  
* ​View Balances: Check the Aggregated Net Balances section to view updated net financial standings across the group.  
* ​View Activity: Review recorded transactions in real time under the Activity Log.

