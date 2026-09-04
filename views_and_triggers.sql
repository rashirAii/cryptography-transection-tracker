-- ====================================================================
-- Cryptocurrency Transaction Tracker Views and Triggers
-- ====================================================================

-- --------------------------------------------------------------------
-- VIEW 1: Wallet Net Balances per Cryptocurrency Asset
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS vw_wallet_balances;

CREATE VIEW vw_wallet_balances AS
WITH incoming AS (
    SELECT 
        receiver_wallet_id AS wallet_id,
        crypto_id,
        SUM(amount) AS total_received
    FROM transactions
    WHERE status = 'COMPLETED' AND receiver_wallet_id IS NOT NULL
    GROUP BY receiver_wallet_id, crypto_id
),
outgoing AS (
    SELECT 
        sender_wallet_id AS wallet_id,
        crypto_id,
        SUM(amount + gas_fee_crypto) AS total_sent
    FROM transactions
    WHERE status = 'COMPLETED' AND sender_wallet_id IS NOT NULL
    GROUP BY sender_wallet_id, crypto_id
)
SELECT 
    w.wallet_id,
    w.user_id,
    u.username,
    w.wallet_address,
    w.wallet_type,
    c.symbol,
    c.name AS crypto_name,
    COALESCE(i.total_received, 0) AS total_received,
    COALESCE(o.total_sent, 0) AS total_sent,
    (COALESCE(i.total_received, 0) - COALESCE(o.total_sent, 0)) AS current_balance
FROM wallets w
JOIN users u ON w.user_id = u.user_id
CROSS JOIN cryptocurrencies c
LEFT JOIN incoming i ON w.wallet_id = i.wallet_id AND c.crypto_id = i.crypto_id
LEFT JOIN outgoing o ON w.wallet_id = o.wallet_id AND c.crypto_id = o.crypto_id
WHERE (COALESCE(i.total_received, 0) - COALESCE(o.total_sent, 0)) > 0;


-- --------------------------------------------------------------------
-- VIEW 2: User Real-Time Portfolio Valuation in USD
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS vw_user_portfolio;

CREATE VIEW vw_user_portfolio AS
WITH latest_rates AS (
    SELECT 
        er.crypto_id,
        er.price_usd
    FROM exchange_rates er
    INNER JOIN (
        SELECT crypto_id, MAX(recorded_at) AS max_date
        FROM exchange_rates
        GROUP BY crypto_id
    ) latest ON er.crypto_id = latest.crypto_id AND er.recorded_at = latest.max_date
)
SELECT 
    wb.user_id,
    wb.username,
    wb.symbol,
    wb.crypto_name,
    SUM(wb.current_balance) AS total_holdings,
    lr.price_usd AS current_price_usd,
    ROUND(SUM(wb.current_balance) * lr.price_usd, 2) AS total_value_usd
FROM vw_wallet_balances wb
JOIN latest_rates lr ON wb.symbol = (SELECT symbol FROM cryptocurrencies WHERE crypto_id = lr.crypto_id)
GROUP BY wb.user_id, wb.username, wb.symbol, wb.crypto_name, lr.price_usd;


-- --------------------------------------------------------------------
-- VIEW 3: Daily Network Traffic & Gas Fee Summary
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS vw_daily_network_activity;

CREATE VIEW vw_daily_network_activity AS
SELECT 
    c.network,
    c.symbol,
    DATE(t.timestamp) AS tx_date,
    COUNT(t.transaction_id) AS total_transactions,
    ROUND(SUM(t.amount), 4) AS total_volume_crypto,
    ROUND(SUM(t.gas_fee_crypto), 6) AS total_gas_crypto,
    ROUND(SUM(t.gas_fee_usd), 2) AS total_gas_usd
FROM transactions t
JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
WHERE t.status = 'COMPLETED'
GROUP BY c.network, c.symbol, DATE(t.timestamp);


-- --------------------------------------------------------------------
-- TRIGGER 1: Automatically Detect & Flag High-Value Transactions (> $100,000)
-- --------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_detect_large_transactions;

CREATE TRIGGER trg_detect_large_transactions
AFTER INSERT ON transactions
FOR EACH ROW
WHEN (
    NEW.amount * (
        SELECT price_usd 
        FROM exchange_rates 
        WHERE crypto_id = NEW.crypto_id 
        ORDER BY recorded_at DESC 
        LIMIT 1
    )
) >= 100000.0
BEGIN
    INSERT INTO fraud_alerts (transaction_id, alert_type, severity, description, created_at)
    VALUES (
        NEW.transaction_id,
        'WHALE_HIGH_VALUE_TX',
        'HIGH',
        'Transaction value exceeds $100,000 threshold. Calculated USD Value: $' || 
        CAST(ROUND(NEW.amount * (SELECT price_usd FROM exchange_rates WHERE crypto_id = NEW.crypto_id ORDER BY recorded_at DESC LIMIT 1), 2) AS TEXT),
        CURRENT_TIMESTAMP
    );
END;
