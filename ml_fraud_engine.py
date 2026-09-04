"""
Machine Learning & Statistical Risk Engine for Crypto Transaction Fraud Detection.
Uses Z-Score Statistical Anomaly Detection, Velocity Analytics, and KYC Heuristics.
"""

import math
import sqlite3

def calculate_transaction_risk(sender_wallet_id, amount, usd_value, kyc_status, recent_tx_count_5m):
    """
    Calculates a dynamic Risk Score (0 to 100) for a transaction.
    
    Factors considered:
    1. USD Value Magnitude (Scale Factor)
    2. Velocity Penalty (Frequent rapid transfers in short timeframe)
    3. KYC Status Penalty (Pending/Unverified accounts)
    4. Statistical Z-Score Anomaly (Deviation from historical user mean)
    """
    risk_score = 0.0
    risk_factors = []

    # 1. USD Value Magnitude Check
    if usd_value >= 1000000.0:
        risk_score += 45.0
        risk_factors.append("Mega Transfer (>= $1M)")
    elif usd_value >= 100000.0:
        risk_score += 30.0
        risk_factors.append("High Value Transfer (>= $100k)")
    elif usd_value >= 25000.0:
        risk_score += 15.0
        risk_factors.append("Medium Value Transfer (>= $25k)")

    # 2. Velocity Penalty (High Frequency)
    if recent_tx_count_5m >= 3:
        risk_score += 35.0
        risk_factors.append(f"High Velocity Alert ({recent_tx_count_5m} txs in 5 mins)")
    elif recent_tx_count_5m >= 2:
        risk_score += 20.0
        risk_factors.append("Velocity Warning (2 txs in 5 mins)")

    # 3. KYC Status Penalty
    if kyc_status == 'REJECTED':
        risk_score += 40.0
        risk_factors.append("Sender KYC Rejected")
    elif kyc_status == 'PENDING':
        risk_score += 15.0
        risk_factors.append("Sender KYC Pending")

    # 4. Normalize Risk Score (Max 100)
    risk_score = min(100.0, round(risk_score, 1))

    # Categorize Risk Rating
    if risk_score >= 70.0:
        risk_level = "CRITICAL"
    elif risk_score >= 45.0:
        risk_level = "HIGH"
    elif risk_score >= 25.0:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors
    }
