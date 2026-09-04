# 🎯 TOP 20 VIVA QUESTIONS & ANSWERS GUIDE
## CryptoPulse - Major Project Viva Preparation

---

### Q1: What is the primary objective of this project?
**Answer**: CryptoPulse is a relational database management system designed to track multi-chain cryptocurrency transactions, calculate dynamic portfolio valuations in USD, monitor gas fees, manage staking rewards, and automatically flag high-risk transactions (> $100,000) using SQL Triggers and Machine Learning risk scoring.

---

### Q2: Why did you use SQLite instead of MySQL or PostgreSQL?
**Answer**: SQLite is a self-contained, serverless, zero-configuration database engine embedded directly into Python. It enforces full ACID compliance and standard SQL syntax while eliminating external server setup, making it lightweight, fast, and 100% portable for local execution and project demonstrations.

---

### Q3: How is Normalization applied in your database schema?
**Answer**: The database adheres strictly to 3rd Normal Form (3NF):
- **1NF**: Atomic values in all columns (no CSV strings in a single column).
- **2NF**: Functional dependency on complete Primary Keys (wallet addresses decoupled from user entities).
- **3NF**: Elimination of transitive dependencies. Price exchange rates are stored separately in `exchange_rates` so `transactions` only reference `crypto_id`.

---

### Q4: How does the Automated Fraud Detection Trigger work?
**Answer**: We created an `AFTER INSERT` database trigger (`trg_detect_large_transactions`) on the `transactions` table. Whenever a new transaction is inserted, the trigger calculates `amount * latest_usd_price`. If the total USD value is $\ge \$100,000$, it automatically inserts an audit row into the `fraud_alerts` table.

---

### Q5: What advanced SQL concepts did you implement?
**Answer**:
1. **Window Functions**: `SUM(amount) OVER (PARTITION BY wallet_id ORDER BY timestamp)` for cumulative running balance calculations.
2. **Common Table Expressions (CTEs)**: Used in self-join queries for detecting high-velocity rapid transfers (< 5 minutes apart).
3. **Database Views**: `vw_user_portfolio` and `vw_wallet_balances` for dynamic real-time reporting.
4. **Database Indexes**: Indexes on `sender_wallet_id`, `crypto_id`, and `timestamp` for $O(1)$ / $O(\log N)$ query optimization.

---

### Q6: How does the Machine Learning Risk Engine work?
**Answer**: The risk engine calculates a dynamic **Risk Score (0 - 100)** evaluating 4 key factors:
1. Transaction USD Magnitude
2. Transaction Velocity (frequency in past 5 minutes)
3. Sender KYC Compliance Status
4. Statistical Z-score deviation from user history.

---

### Q7: How do you handle live market price updates?
**Answer**: The system integrates with the public **CoinGecko REST API** (`/api/sync-prices`). When triggered, it fetches real-time prices for BTC, ETH, SOL, USDT, etc., and inserts new timestamped records into the `exchange_rates` table.

---

### Q8: What is the purpose of the Foreign Key `ON DELETE CASCADE` constraint?
**Answer**: It maintains referential integrity. If a user account is deleted from `users`, all associated records in `wallets` are automatically purged without leaving orphaned records.

---

### Q9: How do you prevent SQL Injection in your application?
**Answer**: In `app.py`, all SQL queries use parameterized prepared statements (e.g., `cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))`). In the SQL Playground, input is restricted strictly to read-only `SELECT` and `WITH` statements.

---

### Q10: What are Database Views and why did you use them?
**Answer**: A View is a virtual table based on the result-set of an SQL statement. We used `vw_user_portfolio` so complex multi-table JOINs and pricing calculations don't need to be rewritten repeatedly by application developers.

---

### Q11: How do you calculate user net worth in USD?
**Answer**: By joining `vw_wallet_balances` with the latest timestamped `price_usd` from `exchange_rates` using a `CROSS JOIN` subquery with `GROUP BY crypto_id HAVING max(recorded_at)`.

---

### Q12: What web framework is used for the backend?
**Answer**: Python Flask, a micro web framework that handles HTTP REST API endpoints (`/api/stats`, `/api/transactions`, `/api/query`) and renders Jinja2 HTML templates.

---

### Q13: How is the frontend designed?
**Answer**: Single Page Application (SPA) style design built using HTML5, Tailwind CSS (Dark Glassmorphism UI), JavaScript ES6 (`fetch` API), FontAwesome icons, and Chart.js for data visualization.

---

### Q14: What happens when a user claims a Staking Reward?
**Answer**: The backend API updates the `reward_earned` column in `staking_rewards` and automatically generates a corresponding transaction record with `tx_type = 'STAKING_REWARD'` in `transactions`.

---

### Q15: How can you export reports from the system?
**Answer**: The system provides two export mechanisms:
1. **CSV Export**: `/api/export/transactions` generates a downloadable `.csv` spreadsheet.
2. **Audit Certificate**: `/api/export/audit-report` generates a printable HTML/PDF compliance certificate.

---

### Q16: What is Indexing and which columns are indexed in your schema?
**Answer**: Indexing creates B-Tree data structures to speed up data retrieval. We created indexes on `sender_wallet_id`, `receiver_wallet_id`, `crypto_id`, and `timestamp`.

---

### Q17: What is the difference between a Database Trigger and a Stored Procedure?
**Answer**: A Trigger is automatically invoked by the DBMS in response to a specified event (INSERT, UPDATE, DELETE). A Stored Procedure must be explicitly called by an application or user.

---

### Q18: What is ACID compliance in SQLite?
**Answer**:
- **Atomicity**: Transactions are all-or-nothing.
- **Consistency**: Constraints (PK, FK, CHECK) are enforced.
- **Isolation**: Concurrent reads/writes don't corrupt data.
- **Durability**: Committed data persists on disk.

---

### Q19: What are the future enhancements for this project?
**Answer**: Live Blockchain Node streaming via Web3.js, Docker containerization, PostgreSQL cluster migration, and Deep Learning model integration for fraud prediction.

---

### Q20: How do you run the project locally?
**Answer**: Run `python run_web_app.py` or double-click `start_app.bat` to launch the Flask server on `http://127.0.0.1:5000`.
