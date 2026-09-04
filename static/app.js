// CryptoPulse Web Application Frontend Logic

let priceChartInstance = null;
let allTransactions = [];
let cryptosList = [];

document.addEventListener("DOMContentLoaded", () => {
    loadStats();
    loadTransactions();
    loadPortfolio();
    loadStaking();
    loadAlerts();
    loadWalletsAndCryptos();
    loadCharts();

    setInterval(() => {
        loadStats();
        loadTransactions();
        loadPortfolio();
        loadStaking();
        loadAlerts();
    }, 15000);
});

// Sync Live Prices from CoinGecko API
async function syncLivePrices() {
    showToast("🔄 Syncing Prices...", "Fetching live market rates from CoinGecko API", "success");
    try {
        const res = await fetch("/api/sync-prices", { method: "POST" });
        const data = await res.json();
        if (res.ok) {
            showToast("✅ Rates Updated!", "Successfully synced live cryptocurrency prices.", "success");
            loadStats();
            loadWalletsAndCryptos();
            loadTransactions();
            loadPortfolio();
        } else {
            showToast("❌ Sync Error", data.error || "Failed to sync rates", "danger");
        }
    } catch (err) {
        showToast("❌ Error", "Network error syncing prices", "danger");
    }
}

// Load KPI Stats
async function loadStats() {
    try {
        const res = await fetch("/api/stats");
        const data = await res.json();
        
        document.getElementById("stat-volume").innerText = "$" + Number(data.total_volume_usd).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById("stat-users-wallets").innerText = `${data.total_users} / ${data.total_wallets}`;
        document.getElementById("stat-gas").innerText = "$" + Number(data.total_gas_usd).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        document.getElementById("stat-rewards").innerText = `${data.total_staking_rewards} Crypto`;
        document.getElementById("stat-alerts").innerText = data.total_alerts;
    } catch (err) {
        console.error("Error loading stats:", err);
    }
}

// Load Transactions
async function loadTransactions() {
    try {
        const res = await fetch("/api/transactions");
        allTransactions = await res.json();
        renderTransactionsTable(allTransactions);
    } catch (err) {
        console.error("Error loading transactions:", err);
    }
}

function renderTransactionsTable(txs) {
    const tbody = document.getElementById("txs-table-body");
    tbody.innerHTML = "";

    if (txs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center py-6 text-gray-500">No transactions recorded yet.</td></tr>`;
        return;
    }

    txs.forEach(tx => {
        const tr = document.createElement("tr");
        tr.className = "hover:bg-gray-800/40 transition duration-150";
        
        const shortHash = tx.tx_hash.substring(0, 10) + "..." + tx.tx_hash.substring(tx.tx_hash.length - 4);
        
        let typeBadge = "";
        if (tx.tx_type === 'DEPOSIT') typeBadge = `<span class="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-xs border border-emerald-500/20 font-semibold">DEPOSIT</span>`;
        else if (tx.tx_type === 'TRANSFER') typeBadge = `<span class="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-xs border border-blue-500/20 font-semibold">TRANSFER</span>`;
        else if (tx.tx_type === 'SWAP') typeBadge = `<span class="bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded text-xs border border-purple-500/20 font-semibold">SWAP</span>`;
        else if (tx.tx_type === 'STAKING_REWARD') typeBadge = `<span class="bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded text-xs border border-amber-500/20 font-semibold">REWARD</span>`;
        else typeBadge = `<span class="bg-gray-500/10 text-gray-400 px-2 py-0.5 rounded text-xs border border-gray-500/20 font-semibold">${tx.tx_type}</span>`;

        // ML Risk Badge
        let riskBadge = "";
        if (tx.risk_level === 'CRITICAL' || tx.risk_level === 'HIGH') {
            riskBadge = `<span class="bg-red-500/20 text-red-400 px-2 py-0.5 rounded text-xs font-bold border border-red-500/30" title="${tx.risk_factors ? tx.risk_factors.join(', ') : ''}"><i class="fa-solid fa-triangle-exclamation mr-1"></i>${tx.risk_level} (${tx.risk_score})</span>`;
        } else if (tx.risk_level === 'MEDIUM') {
            riskBadge = `<span class="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded text-xs font-semibold border border-amber-500/30">${tx.risk_level} (${tx.risk_score})</span>`;
        } else {
            riskBadge = `<span class="bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded text-xs font-medium border border-emerald-500/20">LOW (${tx.risk_score || 0})</span>`;
        }

        tr.innerHTML = `
            <td class="py-3 font-mono text-xs text-blue-400 flex items-center gap-1">
                <span>${shortHash}</span>
                <button onclick="navigator.clipboard.writeText('${tx.tx_hash}')" title="Copy Hash" class="hover:text-white"><i class="fa-regular fa-copy"></i></button>
            </td>
            <td class="py-3">${typeBadge}</td>
            <td class="py-3">${riskBadge}</td>
            <td class="py-3 font-medium text-gray-300">${tx.sender_user}</td>
            <td class="py-3 font-medium text-gray-300">${tx.receiver_user}</td>
            <td class="py-3 font-bold text-white">${tx.amount} <span class="text-xs font-normal text-gray-400">${tx.symbol}</span></td>
            <td class="py-3 text-emerald-400 font-semibold">$${Number(tx.estimated_usd).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
            <td class="py-3 text-xs text-gray-400">$${tx.gas_fee_usd}</td>
            <td class="py-3 text-xs text-gray-500">${tx.timestamp}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterTransactions() {
    const q = document.getElementById("table-search").value.toLowerCase();
    const filtered = allTransactions.filter(tx => 
        tx.tx_hash.toLowerCase().includes(q) ||
        tx.sender_user.toLowerCase().includes(q) ||
        tx.receiver_user.toLowerCase().includes(q) ||
        tx.symbol.toLowerCase().includes(q) ||
        tx.tx_type.toLowerCase().includes(q) ||
        (tx.risk_level && tx.risk_level.toLowerCase().includes(q))
    );
    renderTransactionsTable(filtered);
}

// Load User Portfolio
async function loadPortfolio() {
    try {
        const res = await fetch("/api/portfolio");
        const data = await res.json();
        const tbody = document.getElementById("portfolio-table-body");
        tbody.innerHTML = "";

        data.forEach(item => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-gray-800/40 transition duration-150";
            tr.innerHTML = `
                <td class="py-3 font-semibold text-white">${item.username}</td>
                <td class="py-3"><span class="bg-gray-800 text-blue-400 px-2 py-1 rounded text-xs font-mono">${item.symbol}</span></td>
                <td class="py-3 text-gray-300">${item.crypto_name}</td>
                <td class="py-3 font-bold text-gray-200">${item.total_holdings}</td>
                <td class="py-3 text-gray-400">$${Number(item.current_price_usd).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                <td class="py-3 text-emerald-400 font-bold">$${Number(item.total_value_usd).toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error loading portfolio:", err);
    }
}

// Load Staking Positions
async function loadStaking() {
    try {
        const res = await fetch("/api/staking");
        const data = await res.json();
        const tbody = document.getElementById("staking-table-body");
        tbody.innerHTML = "";

        data.forEach(item => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-gray-800/40 transition duration-150";
            tr.innerHTML = `
                <td class="py-3 font-semibold text-white">${item.username}</td>
                <td class="py-3"><span class="bg-gray-800 text-purple-400 px-2 py-1 rounded text-xs font-mono">${item.symbol}</span></td>
                <td class="py-3 font-bold text-gray-200">${item.staked_amount} ${item.symbol}</td>
                <td class="py-3 text-emerald-400 font-bold">${item.apy_percentage}% APY</td>
                <td class="py-3 text-amber-400 font-semibold">${item.reward_earned} ${item.symbol}</td>
                <td class="py-3 text-xs text-gray-300">${item.annual_projected_crypto} ${item.symbol} ($${item.annual_projected_usd})</td>
                <td class="py-3">
                    <button onclick="claimStakingReward(${item.staking_id})" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow">
                        Claim +0.1 Reward
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error loading staking:", err);
    }
}

async function claimStakingReward(stakingId) {
    try {
        const res = await fetch("/api/staking/claim", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ staking_id: stakingId, claim_amount: 0.1 })
        });
        const data = await res.json();
        if (res.ok) {
            showToast("🎉 Reward Claimed!", data.message, "success");
            loadStats();
            loadStaking();
            loadTransactions();
        } else {
            showToast("❌ Claim Error", data.error, "danger");
        }
    } catch (err) {
        showToast("❌ Error", "Network error", "danger");
    }
}

// Load Fraud Alerts
async function loadAlerts() {
    try {
        const res = await fetch("/api/alerts");
        const data = await res.json();
        const tbody = document.getElementById("alerts-table-body");
        tbody.innerHTML = "";

        data.forEach(alert => {
            const tr = document.createElement("tr");
            tr.className = "hover:bg-gray-800/40 transition duration-150 border-l-2 border-red-500";
            tr.innerHTML = `
                <td class="py-3 font-mono text-xs text-red-400 font-bold">#${alert.alert_id}</td>
                <td class="py-3"><span class="bg-red-500/20 text-red-400 px-2 py-0.5 rounded text-xs font-bold border border-red-500/30">${alert.severity}</span></td>
                <td class="py-3 font-semibold text-gray-200">${alert.alert_type}</td>
                <td class="py-3 font-mono text-xs text-gray-400">${alert.tx_hash.substring(0, 12)}...</td>
                <td class="py-3 text-xs text-gray-300">${alert.description}</td>
                <td class="py-3 text-xs text-gray-500">${alert.created_at}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error loading alerts:", err);
    }
}

// Dropdowns & Calculator
async function loadWalletsAndCryptos() {
    try {
        const [wRes, cRes] = await Promise.all([fetch("/api/wallets"), fetch("/api/cryptos")]);
        const wallets = await wRes.json();
        cryptosList = await cRes.json();

        const senderSel = document.getElementById("modalSender");
        const recvSel = document.getElementById("modalReceiver");
        const cryptoSel = document.getElementById("modalCrypto");
        const calcSel = document.getElementById("calcAsset");

        senderSel.innerHTML = `<option value="">External Deposit / Off-chain Exchange</option>`;
        recvSel.innerHTML = `<option value="">External Off-ramp / DeFi Protocol</option>`;
        cryptoSel.innerHTML = "";
        calcSel.innerHTML = "";

        wallets.forEach(w => {
            const opt1 = document.createElement("option");
            opt1.value = w.wallet_id;
            opt1.innerText = `${w.username} (${w.wallet_label} - ${w.wallet_type})`;
            senderSel.appendChild(opt1);

            const opt2 = document.createElement("option");
            opt2.value = w.wallet_id;
            opt2.innerText = `${w.username} (${w.wallet_label} - ${w.wallet_type})`;
            recvSel.appendChild(opt2);
        });

        cryptosList.forEach(c => {
            const opt1 = document.createElement("option");
            opt1.value = c.crypto_id;
            opt1.innerText = `${c.symbol} - ${c.name} ($${c.price_usd})`;
            cryptoSel.appendChild(opt1);

            const opt2 = document.createElement("option");
            opt2.value = c.symbol;
            opt2.innerText = `${c.symbol} (${c.name})`;
            calcSel.appendChild(opt2);
        });

        calculateConversion();
    } catch (err) {
        console.error("Error loading dropdowns:", err);
    }
}

function calculateConversion() {
    const amount = parseFloat(document.getElementById("calcAmount").value) || 0;
    const symbol = document.getElementById("calcAsset").value;
    const found = cryptosList.find(c => c.symbol === symbol);
    const rate = found ? found.price_usd : 1.0;
    const total = (amount * rate).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    document.getElementById("calcResult").innerText = `$${total} USD`;
}

// SQL Playground
function loadSqlTemplate(type) {
    const consoleEl = document.getElementById("sqlConsole");
    if (type === 'whale') {
        consoleEl.value = `SELECT t.tx_hash, c.symbol, t.amount, er.price_usd, ROUND(t.amount * er.price_usd, 2) AS estimated_usd
FROM transactions t
JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
CROSS JOIN (SELECT crypto_id, price_usd FROM exchange_rates GROUP BY crypto_id HAVING max(recorded_at)) er ON t.crypto_id = er.crypto_id
WHERE (t.amount * er.price_usd) >= 50000.0
ORDER BY estimated_usd DESC;`;
    } else if (type === 'velocity') {
        consoleEl.value = `WITH user_txs AS (
    SELECT t.transaction_id, u.username, t.timestamp, t.amount, c.symbol
    FROM transactions t
    JOIN wallets w ON t.sender_wallet_id = w.wallet_id
    JOIN users u ON w.user_id = u.user_id
    JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id
)
SELECT t1.username, t1.symbol, t1.timestamp AS tx1_time, t2.timestamp AS tx2_time, 'High Velocity (< 5 Mins)' AS alert
FROM user_txs t1
JOIN user_txs t2 ON t1.username = t2.username AND t1.transaction_id < t2.transaction_id
WHERE (JULIANDAY(t2.timestamp) - JULIANDAY(t1.timestamp)) * 24 * 60 <= 5.0;`;
    } else if (type === 'running') {
        consoleEl.value = `SELECT u.username, c.symbol, t.timestamp, t.amount,
       SUM(t.amount) OVER (PARTITION BY u.user_id, c.crypto_id ORDER BY t.timestamp) AS cumulative_crypto
FROM transactions t
JOIN wallets w ON t.receiver_wallet_id = w.wallet_id
JOIN users u ON w.user_id = u.user_id
JOIN cryptocurrencies c ON t.crypto_id = c.crypto_id;`;
    } else if (type === 'gas') {
        consoleEl.value = `SELECT u.username, u.country, COUNT(t.transaction_id) AS tx_count, ROUND(SUM(t.gas_fee_usd), 2) AS total_gas_usd
FROM users u
JOIN wallets w ON u.user_id = w.user_id
JOIN transactions t ON w.wallet_id = t.sender_wallet_id
GROUP BY u.user_id ORDER BY total_gas_usd DESC;`;
    }
}

async function executePlaygroundQuery() {
    const query = document.getElementById("sqlConsole").value.trim();
    const resultsDiv = document.getElementById("queryResults");

    if (!query) {
        resultsDiv.innerHTML = `<p class="text-xs text-red-400">Please enter a SQL query.</p>`;
        return;
    }

    resultsDiv.innerHTML = `<p class="text-xs text-blue-400">Executing SQL Query...</p>`;

    try {
        const res = await fetch("/api/query", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        });
        const data = await res.json();

        if (res.ok) {
            if (data.rows.length === 0) {
                resultsDiv.innerHTML = `<p class="text-xs text-amber-400">Query executed successfully. 0 rows returned.</p>`;
                return;
            }

            let tableHtml = `<table class="w-full text-left border-collapse text-xs font-mono"><thead class="text-gray-400 border-b border-gray-800"><tr>`;
            data.headers.forEach(h => tableHtml += `<th class="pb-2 pr-4 font-semibold">${h}</th>`);
            tableHtml += `</tr></thead><tbody class="divide-y divide-gray-800/50">`;

            data.rows.forEach(row => {
                tableHtml += `<tr class="hover:bg-gray-800/30">`;
                row.forEach(val => tableHtml += `<td class="py-2 pr-4 text-gray-200">${val !== null ? val : 'NULL'}</td>`);
                tableHtml += `</tr>`;
            });
            tableHtml += `</tbody></table><p class="text-[11px] text-gray-500 mt-2">Fetched ${data.count} rows.</p>`;
            resultsDiv.innerHTML = tableHtml;
        } else {
            resultsDiv.innerHTML = `<p class="text-xs text-red-400 font-mono">SQL Error: ${data.error}</p>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = `<p class="text-xs text-red-400">Network error executing query.</p>`;
    }
}

// Charts
async function loadCharts() {
    try {
        const res = await fetch("/api/chart-data");
        const rawData = await res.json();

        const dates = [...new Set(rawData.map(d => d.recorded_at.split(" ")[0]))];
        const btcData = rawData.filter(d => d.symbol === 'BTC').map(d => d.price_usd);
        const ethData = rawData.filter(d => d.symbol === 'ETH').map(d => d.price_usd);
        const solData = rawData.filter(d => d.symbol === 'SOL').map(d => d.price_usd);

        const ctx1 = document.getElementById('priceChart').getContext('2d');
        priceChartInstance = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    { label: 'BTC ($)', data: btcData, borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', tension: 0.3, fill: true },
                    { label: 'ETH ($)', data: ethData, borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', tension: 0.3, fill: true },
                    { label: 'SOL ($)', data: solData, borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', tension: 0.3, fill: true }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#9ca3af', font: { size: 11 } } } },
                scales: {
                    x: { ticks: { color: '#6b7280' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { ticks: { color: '#6b7280' }, grid: { color: 'rgba(255,255,255,0.05)' } }
                }
            }
        });
    } catch (err) {
        console.error("Error initializing price chart:", err);
    }
}

// Modals
function openTxModal() { document.getElementById("txModal").classList.remove("hidden"); }
function closeTxModal() { document.getElementById("txModal").classList.add("hidden"); }
function openUserModal() { document.getElementById("userModal").classList.remove("hidden"); }
function closeUserModal() { document.getElementById("userModal").classList.add("hidden"); }

// Submit User
async function submitNewUser(e) {
    e.preventDefault();
    const username = document.getElementById("userUsername").value.trim();
    const email = document.getElementById("userEmail").value.trim();
    const country = document.getElementById("userCountry").value.trim();
    const kyc = document.getElementById("userKyc").value;

    try {
        const uRes = await fetch("/api/users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, country, kyc_status: kyc })
        });
        const uData = await uRes.json();
        if (uRes.ok) {
            await fetch("/api/wallets", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: uData.user_id, wallet_label: `${username} Wallet`, wallet_type: "HOT" })
            });

            closeUserModal();
            showToast("✅ User & Wallet Registered!", `User '${username}' created with auto-generated wallet.`, "success");
            loadStats();
            loadWalletsAndCryptos();
        } else {
            showToast("❌ User Registration Failed", uData.error, "danger");
        }
    } catch (err) {
        showToast("❌ Error", "Network error", "danger");
    }
}

// Submit Transaction
async function submitTransaction(e) {
    e.preventDefault();
    const sender = document.getElementById("modalSender").value || null;
    const receiver = document.getElementById("modalReceiver").value || null;
    const crypto_id = parseInt(document.getElementById("modalCrypto").value);
    const tx_type = document.getElementById("modalType").value;
    const amount = parseFloat(document.getElementById("modalAmount").value);

    try {
        const res = await fetch("/api/transactions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                sender_wallet_id: sender,
                receiver_wallet_id: receiver,
                crypto_id: crypto_id,
                tx_type: tx_type,
                amount: amount
            })
        });

        const data = await res.json();
        if (res.ok) {
            closeTxModal();
            showToast("✅ Transaction Executed!", `Tx Hash: ${data.tx_hash.substring(0, 16)}...`, "success");

            if (data.fraud_alert_triggered) {
                showToast("🚨 AML FRAUD ALERT FIRED!", `High Risk Transaction > $100k detected & logged!`, "danger");
            }

            loadStats();
            loadTransactions();
            loadPortfolio();
            loadAlerts();
        } else {
            showToast("❌ Transaction Failed", data.error || "Execution error", "danger");
        }
    } catch (err) {
        showToast("❌ Error", "Network error", "danger");
    }
}

// UI Tabs Switcher
function switchTab(tabName) {
    ['txs', 'portfolio', 'staking', 'playground', 'alerts'].forEach(t => {
        document.getElementById(`content-${t}`).classList.add("hidden");
        document.getElementById(`tab-${t}`).className = "px-4 py-2 text-xs font-semibold rounded-lg bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white transition";
    });

    document.getElementById(`content-${tabName}`).classList.remove("hidden");
    document.getElementById(`tab-${tabName}`).className = "px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white transition";

    document.getElementById("search-container").style.display = (tabName === 'txs') ? 'block' : 'none';
}

// Toast Notifications
function showToast(title, message, type = "success") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    
    const bgColor = type === "success" ? "bg-emerald-900/90 border-emerald-500 text-emerald-200" : "bg-red-900/90 border-red-500 text-red-200 glow-alert";
    
    toast.className = `${bgColor} border px-4 py-3 rounded-xl shadow-2xl backdrop-blur-md flex items-center space-x-3 transition-all duration-300 transform translate-y-2 opacity-0`;
    toast.innerHTML = `
        <div>
            <h4 class="font-bold text-sm">${title}</h4>
            <p class="text-xs opacity-90">${message}</p>
        </div>
    `;

    container.appendChild(toast);

    setTimeout(() => toast.classList.remove("translate-y-2", "opacity-0"), 50);
    setTimeout(() => {
        toast.classList.add("opacity-0", "translate-y-2");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
