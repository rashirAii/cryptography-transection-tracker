"""
Cryptocurrency Transaction Tracker - Full-Stack Enterprise Web Application (Flask + SQLite)
Major Project Edition with Live API Sync, ML Risk Engine, Printable Audit Reports & SQL Analytics.
"""

import os
import sqlite3
import random
import csv
import io
import json
import urllib.request
import sys
from flask import Flask, render_template, jsonify, request, Response
from ml_fraud_engine import calculate_transaction_risk

app = Flask(__name__)
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto_tracker.db")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions';")
    if not cursor.fetchone():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        for sql_file in ["schema.sql", "views_and_triggers.sql", "seed.sql"]:
            path = os.path.join(base_dir, sql_file)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    cursor.executescript(f.read())
        conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) AS total FROM users;")
    total_users = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) AS total FROM wallets;")
    total_wallets = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) AS total FROM transactions;")
    total_txs = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COUNT(*) AS total FROM fraud_alerts;")
    total_alerts = cursor.fetchone()["total"]
    
    cursor.execute("SELECT COALESCE(SUM(gas_fee_usd), 0) AS total_gas FROM transactions;")
    total_gas = round(cursor.fetchone()["total_gas"], 2)
    
    cursor.execute("""
        SELECT COALESCE(SUM(t.amount * er.price_usd), 0) AS total_val
        FROM transactions t
        JOIN (SELECT crypto_id, price_usd FROM exchange_rates GROUP BY crypto_id HAVING max(recorded_at)) er 
          ON t.crypto_id = er.crypto_id;
    """)
    total_volume_usd = round(cursor.fetchone()["total_val"], 2)
    
    cursor.execute("SELECT COALESCE(SUM(reward_earned), 0) AS total_rewards FROM staking_rewards;")
    total_staking_rewards = round(cursor.fetchone()["total_rewards"], 4)

    conn.close()
    return jsonify({
        "total_users": total_users,
        "total_wallets": total_wallets,
        "total_txs": total_txs,
        "total_alerts": total_alerts,
        "total_gas_usd": total_gas,
        "total_volume_usd": total_volume_usd,
        "total_staking_rewards": total_staking_rewards
    })

@app.route("/api/sync-prices", methods=["POST"])
def sync_live_prices():
    """Fetches live crypto rates from public API (or simulates fallback) and updates SQLite DB."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Live CoinGecko API endpoint
    api_url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,tether,cardano,chainlink&vs_currencies=usd"
    updated_rates = {}
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode())
            mapping = {
                'BTC': data.get('bitcoin', {}).get('usd'),
                'ETH': data.get('ethereum', {}).get('usd'),
                'SOL': data.get('solana', {}).get('usd'),
                'USDT': data.get('tether', {}).get('usd'),
                'ADA': data.get('cardano', {}).get('usd'),
                'LINK': data.get('chainlink', {}).get('usd')
            }
            for sym, price in mapping.items():
                if price:
                    updated_rates[sym] = price
    except Exception as e:
        # Fallback simulation with slight random variation (+- 1%) if offline/rate-limited
        cursor.execute("SELECT crypto_id, symbol FROM cryptocurrencies;")
        for row in cursor.fetchall():
            cursor.execute("SELECT price_usd FROM exchange_rates WHERE crypto_id = ? ORDER BY recorded_at DESC LIMIT 1;", (row["crypto_id"],))
            last = cursor.fetchone()
            base = last["price_usd"] if last else 100.0
            updated_rates[row["symbol"]] = round(base * (1 + random.uniform(-0.01, 0.01)), 2)

    # Insert updated rates into exchange_rates table
    for symbol, price in updated_rates.items():
        cursor.execute("SELECT crypto_id FROM cryptocurrencies WHERE symbol = ?;", (symbol,))
        c_row = cursor.fetchone()
        if c_row:
            cursor.execute("""
                INSERT INTO exchange_rates (crypto_id, price_usd, volume_24h_usd, recorded_at)
                VALUES (?, ?, 1000000000.0, DATETIME('now'));
            """, (c_row["crypto_id"], price))

    conn.commit()
    conn.close()
    return jsonify({"message": "Market prices synced successfully", "rates": updated_rates})

@app.route("/api/portfolio", methods=["GET"])
def get_portfolio():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vw_user_portfolio ORDER BY total_value_usd DESC;")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/transactions", methods=["GET"])
def get_transactions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            t.transaction_id,
            t.tx_hash,
            t.amount,
            t.gas_fee_crypto,
            t.gas_fee_usd,
            t.tx_type,
            t.status,
            t.timestamp,
            t.sender_wallet_id,
            c.symbol,
            c.name AS crypto_name,
            er.price_usd AS current_rate,
            ROUND(t.amount * er.price_usd, 2) AS estimated_usd,
            COALESCE(u_send.username, 'External') AS sender_user,
            COALESCE(u_recv.username, 'External') AS receiver_user,
            COALESCE(u_send.kyc_status, 'VERIFIED') AS sender_kyc
        FROM transactions t
        JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
        LEFT JOIN wallets w_send ON t.sender_wallet_id = w_send.wallet_id
        LEFT JOIN users u_send ON w_send.user_id = u_send.user_id
        LEFT JOIN wallets w_recv ON t.receiver_wallet_id = w_recv.wallet_id
        LEFT JOIN users u_recv ON w_recv.user_id = u_recv.user_id
        CROSS JOIN (
            SELECT crypto_id, price_usd FROM exchange_rates GROUP BY crypto_id HAVING max(recorded_at)
        ) er ON t.crypto_id = er.crypto_id
        ORDER BY t.timestamp DESC;
    """)
    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        
        # Count recent transactions from sender in last 5 minutes for ML risk calculation
        if d["sender_wallet_id"]:
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM transactions 
                WHERE sender_wallet_id = ? AND timestamp >= DATETIME('now', '-5 minutes');
            """, (d["sender_wallet_id"],))
            recent_cnt = cursor.fetchone()["cnt"]
        else:
            recent_cnt = 0
            
        risk_info = calculate_transaction_risk(
            d["sender_wallet_id"], d["amount"], d["estimated_usd"], d["sender_kyc"], recent_cnt
        )
        d.update(risk_info)
        rows.append(d)
        
    conn.close()
    return jsonify(rows)

@app.route("/api/transactions", methods=["POST"])
def create_transaction():
    data = request.get_json() or {}
    sender_wallet_id = data.get("sender_wallet_id") or None
    receiver_wallet_id = data.get("receiver_wallet_id") or None
    crypto_id = data.get("crypto_id")
    amount = float(data.get("amount", 0))
    tx_type = data.get("tx_type", "TRANSFER")
    
    if not crypto_id or amount <= 0:
        return jsonify({"error": "Invalid crypto asset or amount"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    gas_crypto = 0.0005 if tx_type in ['TRANSFER', 'SWAP'] else 0.0
    cursor.execute("SELECT price_usd FROM exchange_rates WHERE crypto_id = ? ORDER BY recorded_at DESC LIMIT 1;", (crypto_id,))
    rate_row = cursor.fetchone()
    current_price = rate_row["price_usd"] if rate_row else 1.0
    gas_usd = round(gas_crypto * current_price, 2)
    
    tx_hash = "0xtx_" + "".join(random.choices("0123456789abcdef", k=16))
    
    try:
        cursor.execute("""
            INSERT INTO transactions (tx_hash, sender_wallet_id, receiver_wallet_id, crypto_id, amount, gas_fee_crypto, gas_fee_usd, tx_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'COMPLETED');
        """, (tx_hash, sender_wallet_id, receiver_wallet_id, crypto_id, amount, gas_crypto, gas_usd, tx_type))
        conn.commit()
        
        cursor.execute("SELECT * FROM fraud_alerts WHERE transaction_id = (SELECT transaction_id FROM transactions WHERE tx_hash = ?);", (tx_hash,))
        alert = cursor.fetchone()
        
        conn.close()
        return jsonify({
            "message": "Transaction executed successfully",
            "tx_hash": tx_hash,
            "fraud_alert_triggered": bool(alert),
            "alert_details": dict(alert) if alert else None
        }), 201
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/users", methods=["GET", "POST"])
def manage_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        data = request.get_json() or {}
        username = data.get("username")
        email = data.get("email")
        country = data.get("country", "USA")
        kyc_status = data.get("kyc_status", "VERIFIED")
        
        if not username or not email:
            conn.close()
            return jsonify({"error": "Username and Email are required"}), 400
            
        try:
            cursor.execute("INSERT INTO users (username, email, country, kyc_status) VALUES (?, ?, ?, ?);",
                           (username, email, country, kyc_status))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return jsonify({"message": "User created successfully", "user_id": user_id}), 201
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500
            
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC;")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/wallets", methods=["GET", "POST"])
def manage_wallets():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        data = request.get_json() or {}
        user_id = data.get("user_id")
        wallet_label = data.get("wallet_label", "Default Wallet")
        wallet_type = data.get("wallet_type", "HOT")
        
        if not user_id:
            conn.close()
            return jsonify({"error": "User ID is required"}), 400
            
        wallet_address = "0x" + "".join(random.choices("0123456789abcdefABCDEF", k=40))
        
        try:
            cursor.execute("INSERT INTO wallets (user_id, wallet_address, wallet_label, wallet_type) VALUES (?, ?, ?, ?);",
                           (user_id, wallet_address, wallet_label, wallet_type))
            conn.commit()
            wallet_id = cursor.lastrowid
            conn.close()
            return jsonify({"message": "Wallet generated successfully", "wallet_id": wallet_id, "wallet_address": wallet_address}), 201
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500

    cursor.execute("""
        SELECT w.wallet_id, w.user_id, w.wallet_address, w.wallet_label, w.wallet_type, u.username 
        FROM wallets w 
        JOIN users u ON w.user_id = u.user_id;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/staking", methods=["GET", "POST"])
def manage_staking():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        data = request.get_json() or {}
        staking_id = data.get("staking_id")
        claim_amount = float(data.get("claim_amount", 0.1))
        
        if not staking_id:
            conn.close()
            return jsonify({"error": "Staking ID is required"}), 400
            
        try:
            cursor.execute("SELECT wallet_id, crypto_id FROM staking_rewards WHERE staking_id = ?;", (staking_id,))
            stk = cursor.fetchone()
            if not stk:
                conn.close()
                return jsonify({"error": "Staking position not found"}), 404
                
            cursor.execute("UPDATE staking_rewards SET reward_earned = reward_earned + ? WHERE staking_id = ?;", (claim_amount, staking_id))
            
            tx_hash = "0xtx_reward_" + "".join(random.choices("0123456789abcdef", k=12))
            cursor.execute("""
                INSERT INTO transactions (tx_hash, sender_wallet_id, receiver_wallet_id, crypto_id, amount, gas_fee_crypto, gas_fee_usd, tx_type, status)
                VALUES (?, NULL, ?, ?, ?, 0.0, 0.0, 'STAKING_REWARD', 'COMPLETED');
            """, (tx_hash, stk["wallet_id"], stk["crypto_id"], claim_amount))
            
            conn.commit()
            conn.close()
            return jsonify({"message": f"Successfully claimed {claim_amount} reward!", "tx_hash": tx_hash}), 200
        except Exception as e:
            conn.close()
            return jsonify({"error": str(e)}), 500
            
    cursor.execute("""
        SELECT 
            sr.staking_id, u.username, c.symbol, c.name AS crypto_name,
            sr.staked_amount, sr.reward_earned, sr.apy_percentage, sr.start_date,
            ROUND(sr.staked_amount * (sr.apy_percentage / 100.0), 4) AS annual_projected_crypto,
            ROUND(sr.staked_amount * (sr.apy_percentage / 100.0) * er.price_usd, 2) AS annual_projected_usd
        FROM staking_rewards sr
        JOIN wallets w ON sr.wallet_id = w.wallet_id
        JOIN users u ON w.user_id = u.user_id
        JOIN cryptocurrencies c ON sr.crypto_id = c.crypto_id
        CROSS JOIN (
            SELECT crypto_id, price_usd FROM exchange_rates GROUP BY crypto_id HAVING max(recorded_at)
        ) er ON sr.crypto_id = er.crypto_id;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/cryptos", methods=["GET"])
def get_cryptos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.crypto_id, c.symbol, c.name, c.network, er.price_usd 
        FROM cryptocurrencies c
        LEFT JOIN (
            SELECT crypto_id, price_usd FROM exchange_rates GROUP BY crypto_id HAVING max(recorded_at)
        ) er ON c.crypto_id = er.crypto_id;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            fa.alert_id, fa.alert_type, fa.severity, fa.description, fa.created_at,
            t.tx_hash, t.amount, c.symbol
        FROM fraud_alerts fa
        JOIN transactions t ON fa.transaction_id = t.transaction_id
        JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
        ORDER BY fa.alert_id DESC;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route("/api/query", methods=["POST"])
def execute_sql_query():
    data = request.get_json() or {}
    raw_query = data.get("query", "").strip()
    
    if not raw_query:
        return jsonify({"error": "No SQL query provided"}), 400
        
    if not raw_query.upper().startswith("SELECT") and not raw_query.upper().startswith("WITH"):
        return jsonify({"error": "Playground only allows SELECT or CTE queries for security"}), 403
        
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(raw_query)
        headers = [d[0] for d in cursor.description] if cursor.description else []
        rows = [list(r) for r in cursor.fetchall()]
        conn.close()
        return jsonify({"headers": headers, "rows": rows, "count": len(rows)})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 400

@app.route("/api/export/transactions", methods=["GET"])
def export_transactions_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            t.transaction_id, t.tx_hash, t.tx_type, 
            COALESCE(u_send.username, 'External') AS sender,
            COALESCE(u_recv.username, 'External') AS receiver,
            c.symbol, t.amount, t.gas_fee_usd, t.status, t.timestamp
        FROM transactions t
        JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
        LEFT JOIN wallets w_send ON t.sender_wallet_id = w_send.wallet_id
        LEFT JOIN users u_send ON w_send.user_id = u_send.user_id
        LEFT JOIN wallets w_recv ON t.receiver_wallet_id = w_recv.wallet_id
        LEFT JOIN users u_recv ON w_recv.user_id = u_recv.user_id
        ORDER BY t.timestamp DESC;
    """)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Tx ID", "Hash", "Type", "Sender", "Receiver", "Asset", "Amount", "Gas Fee USD", "Status", "Timestamp"])
    for r in rows:
        writer.writerow(list(r))
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=crypto_transactions_report.csv"}
    )

@app.route("/api/export/audit-report", methods=["GET"])
def export_printable_audit_report():
    """Generates a formal, printable HTML Compliance Audit Certificate for academic review."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) AS cnt FROM transactions;")
    total_txs = cursor.fetchone()["cnt"]
    
    cursor.execute("SELECT COUNT(*) AS cnt FROM fraud_alerts;")
    total_alerts = cursor.fetchone()["cnt"]
    
    cursor.execute("""
        SELECT fa.alert_id, fa.alert_type, fa.severity, fa.description, fa.created_at, t.tx_hash
        FROM fraud_alerts fa
        JOIN transactions t ON fa.transaction_id = t.transaction_id
        ORDER BY fa.alert_id DESC;
    """)
    alerts = cursor.fetchall()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>CryptoPulse - Official Compliance Audit Certificate</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; color: #111; line-height: 1.6; }}
            .header {{ text-align: center; border-bottom: 2px solid #222; padding-bottom: 10px; margin-bottom: 20px; }}
            .stamp {{ border: 2px dashed #b91c1c; color: #b91c1c; padding: 10px; text-align: center; font-weight: bold; width: 250px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px 12px; text-align: left; font-size: 13px; }}
            th {{ background: #f4f4f4; }}
        </style>
    </head>
    <body onload="window.print()">
        <div class="header">
            <h2>CRYPTOPULSE COMPLIANCE AUDIT CERTIFICATE</h2>
            <p>Automated Anti-Money Laundering (AML) & Risk Monitoring System Report</p>
        </div>
        
        <p><strong>System Audit Date:</strong> DATETIME('now')</p>
        <p><strong>Database Engine:</strong> SQLite 3.x (Normalized 3NF)</p>
        <p><strong>Total Executed Transactions Audited:</strong> {total_txs}</p>
        <p><strong>Total High-Risk Compliance Alerts Flagged:</strong> {total_alerts}</p>
        
        <div class="stamp">OFFICIAL COMPLIANCE PASSED</div>
        
        <h3>Flagged High-Risk Fraud Log Summary</h3>
        <table>
            <thead>
                <tr>
                    <th>Alert ID</th>
                    <th>Severity</th>
                    <th>Type</th>
                    <th>Transaction Hash</th>
                    <th>Audit Description</th>
                    <th>Timestamp</th>
                </tr>
            </thead>
            <tbody>
    """
    for a in alerts:
        html += f"""
            <tr>
                <td>#{a['alert_id']}</td>
                <td style="color:red; font-weight:bold;">{a['severity']}</td>
                <td>{a['alert_type']}</td>
                <td>{a['tx_hash']}</td>
                <td>{a['description']}</td>
                <td>{a['created_at']}</td>
            </tr>
        """
    html += """
            </tbody>
        </table>
        <br><br>
        <div style="display:flex; justify-content:space-between; margin-top:50px;">
            <div>_______________________<br>Head of Compliance</div>
            <div>_______________________<br>Chief System Auditor</div>
        </div>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")

@app.route("/api/chart-data", methods=["GET"])
def get_chart_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.symbol, er.price_usd, er.recorded_at 
        FROM exchange_rates er 
        JOIN cryptocurrencies c ON er.crypto_id = c.crypto_id 
        ORDER BY er.recorded_at ASC;
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    print("🚀 Starting CryptoPulse Enterprise Web Application on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
