-- ====================================================================
-- Cryptocurrency Transaction Tracker Seed Data
-- ====================================================================

-- 1. SEED USERS
INSERT INTO users (user_id, username, email, country, kyc_status, created_at) VALUES
(1, 'alice_crypto', 'alice@blockchain.io', 'USA', 'VERIFIED', '2026-01-10 09:00:00'),
(2, 'bob_trader', 'bob@tradex.uk', 'UK', 'VERIFIED', '2026-02-15 11:30:00'),
(3, 'charlie_hodl', 'charlie@crypto.in', 'India', 'VERIFIED', '2026-03-01 14:20:00'),
(4, 'diana_defi', 'diana@eth.de', 'Germany', 'VERIFIED', '2026-04-12 16:45:00'),
(5, 'satoshi_whale', 'whale@satoshi.jp', 'Japan', 'VERIFIED', '2026-05-20 08:15:00'),
(6, 'eva_quant', 'eva@singapore.sg', 'Singapore', 'PENDING', '2026-07-01 10:00:00'),
(7, 'frank_newbie', 'frank@toronto.ca', 'Canada', 'REJECTED', '2026-08-15 12:00:00');

-- 2. SEED CRYPTOCURRENCIES
INSERT INTO cryptocurrencies (crypto_id, symbol, name, network, decimals, is_stablecoin) VALUES
(1, 'BTC', 'Bitcoin', 'Bitcoin', 8, 0),
(2, 'ETH', 'Ethereum', 'Ethereum', 18, 0),
(3, 'SOL', 'Solana', 'Solana', 9, 0),
(4, 'USDT', 'Tether USD', 'Ethereum', 6, 1),
(5, 'ADA', 'Cardano', 'Cardano', 6, 0),
(6, 'LINK', 'Chainlink', 'Ethereum', 18, 0);

-- 3. SEED WALLETS
INSERT INTO wallets (wallet_id, user_id, wallet_address, wallet_label, wallet_type, created_at) VALUES
(1, 1, '0xAliceEthereumMainnetHotWallet001', 'Alice Main ETH', 'HOT', '2026-01-11 10:00:00'),
(2, 1, 'bc1qAliceBitcoinColdStorageVault999', 'Alice Cold BTC', 'COLD', '2026-01-12 11:00:00'),
(3, 2, '0xBobTradingAccountBinanceCustody02', 'Bob Exchange Wallet', 'CUSTODIAL', '2026-02-16 12:00:00'),
(4, 3, 'bc1qCharlieIndiaBitcoinHODLVault03', 'Charlie Cold BTC', 'COLD', '2026-03-02 15:00:00'),
(5, 4, '0xDianaDeFiUniswapStakingWallet04', 'Diana DeFi Yield', 'DEFI', '2026-04-13 17:00:00'),
(6, 5, 'bc1qSatoshiWhaleMegaStorageVault05', 'Whale Vault Alpha', 'COLD', '2026-05-21 09:00:00'),
(7, 5, '0xSatoshiWhaleEthHighVolumeWallet', 'Whale ETH Hot', 'HOT', '2026-05-22 09:30:00'),
(8, 6, 'SolEvaSolanaPhantomWalletAddress07', 'Eva Solana Hot', 'HOT', '2026-07-02 10:30:00');

-- 4. SEED HISTORICAL EXCHANGE RATES (USD)
INSERT INTO exchange_rates (rate_id, crypto_id, price_usd, volume_24h_usd, recorded_at) VALUES
(1, 1, 62000.00, 28000000000.0, '2026-09-01 00:00:00'),
(2, 1, 63500.00, 31000000000.0, '2026-09-02 00:00:00'),
(3, 1, 64200.00, 29500000000.0, '2026-09-03 00:00:00'),
(4, 1, 65000.00, 33000000000.0, '2026-09-04 00:00:00'),

(5, 2, 3400.00, 15000000000.0, '2026-09-01 00:00:00'),
(6, 2, 3450.00, 16200000000.0, '2026-09-02 00:00:00'),
(7, 2, 3500.00, 15800000000.0, '2026-09-03 00:00:00'),
(8, 2, 3600.00, 17500000000.0, '2026-09-04 00:00:00'),

(9, 3, 135.00, 4200000000.0, '2026-09-01 00:00:00'),
(10, 3, 140.00, 4800000000.0, '2026-09-02 00:00:00'),
(11, 3, 148.00, 5100000000.0, '2026-09-03 00:00:00'),
(12, 3, 155.00, 5600000000.0, '2026-09-04 00:00:00'),

(13, 4, 1.00, 45000000000.0, '2026-09-04 00:00:00'),
(14, 5, 0.45, 800000000.0, '2026-09-04 00:00:00'),
(15, 6, 18.50, 600000000.0, '2026-09-04 00:00:00');

-- 5. SEED TRANSACTIONS
-- Note: NULL sender = External Deposit; NULL receiver = External Withdrawal/Off-ramp
INSERT INTO transactions (transaction_id, tx_hash, sender_wallet_id, receiver_wallet_id, crypto_id, amount, gas_fee_crypto, gas_fee_usd, tx_type, status, timestamp) VALUES
-- Alice initial deposits & transfers
(1, '0xtx001_alice_btc_deposit', NULL, 2, 1, 5.0, 0.0001, 6.20, 'DEPOSIT', 'COMPLETED', '2026-09-01 08:30:00'),
(2, '0xtx002_alice_eth_deposit', NULL, 1, 2, 25.0, 0.002, 6.80, 'DEPOSIT', 'COMPLETED', '2026-09-01 09:15:00'),
(3, '0xtx003_alice_sends_bob_eth', 1, 3, 2, 5.0, 0.003, 10.35, 'TRANSFER', 'COMPLETED', '2026-09-02 10:00:00'),

-- Satoshi Whale mega transactions
(4, '0xtx004_whale_btc_funding', NULL, 6, 1, 500.0, 0.0005, 31.75, 'DEPOSIT', 'COMPLETED', '2026-09-01 11:00:00'),
(5, '0xtx005_whale_transfers_charlie_btc', 6, 4, 1, 50.0, 0.0004, 25.60, 'TRANSFER', 'COMPLETED', '2026-09-02 14:00:00'),
(6, '0xtx006_whale_eth_funding', NULL, 7, 2, 1000.0, 0.005, 17.50, 'DEPOSIT', 'COMPLETED', '2026-09-02 15:30:00'),

-- Diana DeFi Staking & Swaps
(7, '0xtx007_diana_eth_deposit', NULL, 5, 2, 50.0, 0.004, 14.00, 'DEPOSIT', 'COMPLETED', '2026-09-01 12:00:00'),
(8, '0xtx008_diana_swap_eth_usdt', 5, 5, 4, 34500.0, 0.008, 27.60, 'SWAP', 'COMPLETED', '2026-09-02 16:00:00'),

-- Eva Solana trading
(9, '0xtx009_eva_sol_deposit', NULL, 8, 3, 200.0, 0.000005, 0.0007, 'DEPOSIT', 'COMPLETED', '2026-09-02 08:00:00'),
(10, '0xtx010_eva_sends_diana_sol', 8, 5, 3, 50.0, 0.000005, 0.0007, 'TRANSFER', 'COMPLETED', '2026-09-03 09:30:00'),

-- Whale massive transfer (> $100k alert trigger test)
(11, '0xtx011_whale_mega_transfer_suspicious', 6, 2, 1, 40.0, 0.0006, 39.00, 'TRANSFER', 'COMPLETED', '2026-09-04 10:15:00'),

-- Rapid high frequency transfers (Suspicious Velocity Test)
(12, '0xtx012_rapid_tx_1', 3, 1, 2, 1.0, 0.002, 7.20, 'TRANSFER', 'COMPLETED', '2026-09-04 11:00:00'),
(13, '0xtx013_rapid_tx_2', 3, 1, 2, 1.0, 0.002, 7.20, 'TRANSFER', 'COMPLETED', '2026-09-04 11:02:00'),
(14, '0xtx014_rapid_tx_3', 3, 1, 2, 1.0, 0.002, 7.20, 'TRANSFER', 'COMPLETED', '2026-09-04 11:04:00'),

-- Staking Rewards payout
(15, '0xtx015_diana_staking_reward', NULL, 5, 2, 0.75, 0.0, 0.0, 'STAKING_REWARD', 'COMPLETED', '2026-09-04 12:00:00');

-- 6. SEED STAKING REWARDS
INSERT INTO staking_rewards (staking_id, wallet_id, crypto_id, staked_amount, reward_earned, apy_percentage, start_date) VALUES
(1, 5, 2, 30.0, 0.75, 6.5, '2026-08-01'),
(2, 8, 3, 100.0, 3.20, 7.2, '2026-08-10');
