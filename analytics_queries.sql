-- ====================================================================
-- Cryptocurrency Transaction Tracker - Advanced Analytics Queries
-- ====================================================================

-- --------------------------------------------------------------------
-- QUERY 1: User Portfolio Breakdown & Total Net Worth in USD
-- Demonstrates: Aggregations, Views, JOINs
-- --------------------------------------------------------------------
SELECT 
    username,
    symbol,
    crypto_name,
    total_holdings,
    current_price_usd,
    total_value_usd
FROM vw_user_portfolio
ORDER BY total_value_usd DESC;


-- --------------------------------------------------------------------
-- QUERY 2: Whale Watcher - Top 5 High-Value Transactions (> $50,000)
-- Demonstrates: Subqueries, Price conversion, ORDER BY & LIMIT
-- --------------------------------------------------------------------
SELECT 
    t.tx_hash,
    COALESCE(u_sender.username, 'External Deposit/Exchange') AS sender,
    COALESCE(u_recv.username, 'External Off-ramp/DeFi') AS receiver,
    c.symbol,
    t.amount,
    er.price_usd AS rate_at_time,
    ROUND(t.amount * er.price_usd, 2) AS estimated_tx_value_usd,
    t.tx_type,
    t.timestamp
FROM transactions t
JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
LEFT JOIN wallets w_sender ON t.sender_wallet_id = w_sender.wallet_id
LEFT JOIN users u_sender ON w_sender.user_id = u_sender.user_id
LEFT JOIN wallets w_recv ON t.receiver_wallet_id = w_recv.wallet_id
LEFT JOIN users u_recv ON w_recv.user_id = u_recv.user_id
CROSS JOIN (
    SELECT crypto_id, price_usd 
    FROM exchange_rates 
    GROUP BY crypto_id 
    HAVING max(recorded_at)
) er ON t.crypto_id = er.crypto_id
ORDER BY estimated_tx_value_usd DESC
LIMIT 5;


-- --------------------------------------------------------------------
-- QUERY 3: Cumulative Running Wallet Balance Over Time
-- Demonstrates: Window Functions (SUM OVER ORDER BY), CTEs
-- --------------------------------------------------------------------
WITH wallet_tx_flow AS (
    SELECT 
        w.wallet_id,
        u.username,
        c.symbol,
        t.timestamp,
        CASE 
            WHEN t.receiver_wallet_id = w.wallet_id THEN t.amount
            WHEN t.sender_wallet_id = w.wallet_id THEN -(t.amount + t.gas_fee_crypto)
            ELSE 0 
        END AS net_change
    FROM transactions t
    JOIN wallets w ON t.sender_wallet_id = w.wallet_id OR t.receiver_wallet_id = w.wallet_id
    JOIN users u ON w.user_id = u.user_id
    JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
    WHERE t.status = 'COMPLETED'
)
SELECT 
    username,
    symbol,
    timestamp,
    net_change,
    ROUND(SUM(net_change) OVER (
        PARTITION BY wallet_id, symbol 
        ORDER BY timestamp 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 4) AS running_balance
FROM wallet_tx_flow
ORDER BY username, symbol, timestamp;


-- --------------------------------------------------------------------
-- QUERY 4: Gas Fee Expenditure Leaderboard per User
-- Demonstrates: SUM aggregation, GROUP BY, Formatting
-- --------------------------------------------------------------------
SELECT 
    u.username,
    u.country,
    COUNT(t.transaction_id) AS total_outbound_txs,
    ROUND(SUM(t.gas_fee_usd), 2) AS total_gas_paid_usd
FROM users u
JOIN wallets w ON u.user_id = w.user_id
JOIN transactions t ON w.wallet_id = t.sender_wallet_id
GROUP BY u.user_id, u.username, u.country
ORDER BY total_gas_paid_usd DESC;


-- --------------------------------------------------------------------
-- QUERY 5: Suspicious Activity Detection (High-Velocity Transfers)
-- Identifies wallets performing multiple transactions within a short window (5 mins)
-- Demonstrates: CTE, Self JOIN, Time arithmetic
-- --------------------------------------------------------------------
WITH user_txs AS (
    SELECT 
        t.transaction_id,
        t.sender_wallet_id,
        u.username,
        t.timestamp,
        t.amount,
        c.symbol
    FROM transactions t
    JOIN wallets w ON t.sender_wallet_id = w.wallet_id
    JOIN users u ON w.user_id = u.user_id
    JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
)
SELECT DISTINCT
    t1.username,
    t1.symbol,
    t1.timestamp AS tx1_time,
    t2.timestamp AS tx2_time,
    t1.amount AS tx1_amount,
    t2.amount AS tx2_amount,
    'High Velocity Transfers (< 5 Mins)' AS alert_reason
FROM user_txs t1
JOIN user_txs t2 ON t1.sender_wallet_id = t2.sender_wallet_id 
    AND t1.transaction_id < t2.transaction_id
WHERE (JULIANDAY(t2.timestamp) - JULIANDAY(t1.timestamp)) * 24 * 60 <= 5.0;


-- --------------------------------------------------------------------
-- QUERY 6: Staking Overview & Annual Yield Projections
-- Demonstrates: Financial math, Multi-table JOIN
-- --------------------------------------------------------------------
SELECT 
    u.username,
    c.symbol,
    sr.staked_amount,
    sr.apy_percentage,
    sr.reward_earned AS rewards_collected_to_date,
    ROUND(sr.staked_amount * (sr.apy_percentage / 100.0), 4) AS projected_annual_reward_crypto,
    ROUND(sr.staked_amount * (sr.apy_percentage / 100.0) * er.price_usd, 2) AS projected_annual_reward_usd
FROM staking_rewards sr
JOIN wallets w ON sr.wallet_id = w.wallet_id
JOIN users u ON w.user_id = u.user_id
JOIN cryptocurrencies c ON sr.crypto_id = c.crypto_id
CROSS JOIN (
    SELECT crypto_id, price_usd 
    FROM exchange_rates 
    GROUP BY crypto_id 
    HAVING max(recorded_at)
) er ON sr.crypto_id = er.crypto_id;


-- --------------------------------------------------------------------
-- QUERY 7: Triggered Fraud & Compliance Audit Log
-- Demonstrates: Audit table querying
-- --------------------------------------------------------------------
SELECT 
    fa.alert_id,
    fa.severity,
    fa.alert_type,
    fa.description,
    t.tx_hash,
    t.timestamp AS transaction_time
FROM fraud_alerts fa
JOIN transactions t ON fa.transaction_id = t.transaction_id
ORDER BY fa.alert_id DESC;
