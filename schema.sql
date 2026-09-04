-- ====================================================================
-- Cryptocurrency Transaction Tracker Database Schema
-- Compatible with SQLite, PostgreSQL, and MySQL
-- ====================================================================

-- Drop existing tables if re-initializing
DROP TABLE IF EXISTS fraud_alerts;
DROP TABLE IF EXISTS staking_rewards;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS exchange_rates;
DROP TABLE IF EXISTS wallets;
DROP TABLE IF EXISTS cryptocurrencies;
DROP TABLE IF EXISTS users;

-- 1. USERS TABLE
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(50) DEFAULT 'USA',
    kyc_status VARCHAR(20) CHECK (kyc_status IN ('VERIFIED', 'PENDING', 'REJECTED')) DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. CRYPTOCURRENCIES TABLE
CREATE TABLE cryptocurrencies (
    crypto_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(50) NOT NULL,
    network VARCHAR(50) NOT NULL,
    decimals INTEGER DEFAULT 18,
    is_stablecoin INTEGER DEFAULT 0 CHECK (is_stablecoin IN (0, 1))
);

-- 3. WALLETS TABLE
CREATE TABLE wallets (
    wallet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    wallet_address VARCHAR(100) NOT NULL UNIQUE,
    wallet_label VARCHAR(50),
    wallet_type VARCHAR(20) CHECK (wallet_type IN ('HOT', 'COLD', 'CUSTODIAL', 'DEFI')) DEFAULT 'HOT',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 4. EXCHANGE RATES TABLE (Historical Price Tracking)
CREATE TABLE exchange_rates (
    rate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    crypto_id INTEGER NOT NULL,
    price_usd REAL NOT NULL,
    volume_24h_usd REAL,
    recorded_at DATETIME NOT NULL,
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(crypto_id) ON DELETE CASCADE
);

-- 5. TRANSACTIONS TABLE
CREATE TABLE transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_hash VARCHAR(100) NOT NULL UNIQUE,
    sender_wallet_id INTEGER,
    receiver_wallet_id INTEGER,
    crypto_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    gas_fee_crypto REAL DEFAULT 0.0,
    gas_fee_usd REAL DEFAULT 0.0,
    tx_type VARCHAR(20) CHECK (tx_type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'BUY', 'SELL', 'SWAP', 'STAKING_REWARD')) NOT NULL,
    status VARCHAR(20) CHECK (status IN ('COMPLETED', 'PENDING', 'FAILED')) DEFAULT 'COMPLETED',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_wallet_id) REFERENCES wallets(wallet_id),
    FOREIGN KEY (receiver_wallet_id) REFERENCES wallets(wallet_id),
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(crypto_id)
);

-- 6. STAKING REWARDS TABLE
CREATE TABLE staking_rewards (
    staking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_id INTEGER NOT NULL,
    crypto_id INTEGER NOT NULL,
    staked_amount REAL NOT NULL,
    reward_earned REAL DEFAULT 0.0,
    apy_percentage REAL DEFAULT 5.0,
    start_date DATE NOT NULL,
    FOREIGN KEY (wallet_id) REFERENCES wallets(wallet_id),
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(crypto_id)
);

-- 7. FRAUD ALERTS TABLE
CREATE TABLE fraud_alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE
);

-- Indexes for optimized analytical query execution
CREATE INDEX idx_transactions_sender ON transactions(sender_wallet_id);
CREATE INDEX idx_transactions_receiver ON transactions(receiver_wallet_id);
CREATE INDEX idx_transactions_crypto ON transactions(crypto_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_exchange_rates_crypto_date ON exchange_rates(crypto_id, recorded_at);
