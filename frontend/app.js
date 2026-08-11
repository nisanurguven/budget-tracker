const API_URL = "http://127.0.0.1:8000";

let allExpenses = [];
let expenseChart = null;

// DOM Elemanları
const authContainer = document.getElementById("auth-container");
const dashboardContainer = document.getElementById("dashboard-container");

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const expenseForm = document.getElementById("expense-form");

const loginUsername = document.getElementById("login-username");
const loginPassword = document.getElementById("login-password");
const registerUsername = document.getElementById("register-username");
const registerEmail = document.getElementById("register-email");
const registerPassword = document.getElementById("register-password");
const toRegisterLink = document.getElementById("to-register-link");
const toLoginLink = document.getElementById("to-login-link");

const expenseTitle = document.getElementById("expense-title");
const expenseAmount = document.getElementById("expense-amount");
const expenseCategory = document.getElementById("expense-category");
const expenseDate = document.getElementById("expense-date");

const userNameDisplay = document.getElementById("user-name-display");
const logoutBtn = document.getElementById("logout-btn");
const getAiAdviceBtn = document.getElementById("get-ai-advice-btn");
const aiAdviceResult = document.getElementById("ai-advice-result");
const expenseListBody = document.getElementById("expense-list-body");
const categoryFilter = document.getElementById("category-filter");
const monthFilter = document.getElementById("month-filter");
const totalSpentDisplay = document.getElementById("total-spent-display");

// Formdaki tarih alanına varsayılan olarak bugünü atama
if (expenseDate) {
    expenseDate.value = new Date().toISOString().split('T')[0];
}

// 1. OTURUM KONTROLÜ
function checkAuth() {
    const token = localStorage.getItem("token");
    const username = localStorage.getItem("username");

    if (token) {
        if (authContainer) authContainer.classList.add("hidden");
        if (dashboardContainer) dashboardContainer.classList.remove("hidden");
        if (username && userNameDisplay) userNameDisplay.textContent = username;
        loadExpenses();
    } else {
        if (authContainer) authContainer.classList.remove("hidden");
        if (dashboardContainer) dashboardContainer.classList.add("hidden");
    }
}

// 2. FORM GEÇİŞLERİ (Giriş Yap / Kayıt Ol Ekran Geçişleri)
if (toRegisterLink) {
    toRegisterLink.addEventListener("click", (e) => {
        e.preventDefault();
        if (loginForm) loginForm.classList.add("hidden");
        if (registerForm) registerForm.classList.remove("hidden");
    });
}

if (toLoginLink) {
    toLoginLink.addEventListener("click", (e) => {
        e.preventDefault();
        if (registerForm) registerForm.classList.add("hidden");
        if (loginForm) loginForm.classList.remove("hidden");
    });
}

// 3. KAYIT OLMA
if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
            const response = await fetch(`${API_URL}/users?username=${encodeURIComponent(registerUsername.value)}&email=${encodeURIComponent(registerEmail.value)}&password=${encodeURIComponent(registerPassword.value)}`, {
                method: "POST"
            });
            if (response.ok) {
                alert("Registration successful! You can log in now.");
                registerForm.reset();
                registerForm.classList.add("hidden");
                if (loginForm) loginForm.classList.remove("hidden");
            } else {
                const data = await response.json();
                alert("Error: " + (data.detail || "Registration failed."));
            }
        } catch (error) {
            console.error("Register error:", error);
        }
    });
}

// 4. GİRİŞ YAPMA
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new URLSearchParams();
        formData.append("username", loginUsername.value);
        formData.append("password", loginPassword.value);

        try {
            const response = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                localStorage.setItem("token", data.access_token);
                localStorage.setItem("username", loginUsername.value);
                checkAuth();
            } else {
                alert("Login Error: " + data.detail);
            }
        } catch (error) {
            console.error("Login error:", error);
        }
    });
}

// 5. ÇIKIŞ YAPMA
if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("token");
        localStorage.removeItem("username");
        checkAuth();
    });
}

// 6. HARCAMALARI YÜKLEME
async function loadExpenses() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/expenses`, {
            method: "GET",
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (response.ok) {
            allExpenses = await response.json();
            updateCategoryFilterDropdown();
            renderFilteredExpenses();
        }
    } catch (error) {
        console.error("Load expenses error:", error);
    }
}

// Kategori Açılır Menüsünü Güncelleme
function updateCategoryFilterDropdown() {
    if (!categoryFilter) return;

    const categories = [...new Set(allExpenses.map(e => e.category))];
    const currentSelection = categoryFilter.value;

    categoryFilter.innerHTML = '<option value="all">All Categories</option>';
    categories.forEach(cat => {
        const option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        categoryFilter.appendChild(option);
    });

    if (categories.includes(currentSelection)) {
        categoryFilter.value = currentSelection;
    }
}

// Filtrelenmiş Harcamaları Ekrana Basma, Toplamı ve Grafiği Güncelleme
function renderFilteredExpenses() {
    if (!expenseListBody) return;

    const selectedCat = categoryFilter ? categoryFilter.value : "all";
    const selectedMonth = monthFilter ? monthFilter.value : "";

    const filtered = allExpenses.filter(e => {
        const matchCategory = (selectedCat === "all" || e.category === selectedCat);
        
        let matchMonth = true;
        if (selectedMonth && e.date) {
            matchMonth = e.date.startsWith(selectedMonth);
        }

        return matchCategory && matchMonth;
    });

    // Toplam Harcamayı Hesapla ve Özet Kartına Bas
    const totalSpent = filtered.reduce((sum, e) => sum + (Number(e.amount) || 0), 0);
    if (totalSpentDisplay) {
        totalSpentDisplay.textContent = `$${totalSpent.toFixed(2)}`;
    }

    // Tabloyu Temizle ve Doldur
    expenseListBody.innerHTML = "";
    filtered.forEach(expense => {
        const rawDate = expense.date || "";
        const cleanDate = rawDate.includes("T") ? rawDate.split("T")[0] : rawDate;

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${cleanDate || "N/A"}</td>
            <td>${expense.category}</td>
            <td>${expense.title}</td>
            <td>$${Number(expense.amount).toFixed(2)}</td>
            <td>
                <button onclick="deleteExpense(${expense.id})" style="background-color: #ef4444; padding: 4px 8px; font-size: 12px; color: white; border: none; border-radius: 4px; cursor: pointer;">Delete</button>
            </td>
        `;
        expenseListBody.appendChild(tr);
    });

    // Grafiği Güncelle
    updateExpenseChart(filtered);
}

if (categoryFilter) categoryFilter.addEventListener("change", renderFilteredExpenses);
if (monthFilter) monthFilter.addEventListener("change", renderFilteredExpenses);

// Chart.js Grafiğini Güncelleme
function updateExpenseChart(expensesToDisplay = allExpenses) {
    const ctx = document.getElementById("expense-chart");
    if (!ctx || typeof Chart === "undefined") return;

    const categoryTotals = {};
    expensesToDisplay.forEach(e => {
        const amount = Number(e.amount) || 0;
        const category = e.category ? String(e.category).trim() : "Other";
        categoryTotals[category] = (categoryTotals[category] || 0) + amount;
    });

    const labels = Object.keys(categoryTotals);
    const data = Object.values(categoryTotals);

    if (expenseChart) {
        expenseChart.destroy();
    }

    if (labels.length === 0) return;

    const colors = ["#2563EB", "#16A34A", "#DC2626", "#D97706", "#9333EA", "#0891B2", "#EC4899", "#F97316"];

    expenseChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { position: "bottom" },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = Number(context.raw) || 0;
                            return ` ${context.label}: $${val.toFixed(2)}`;
                        }
                    }
                }
            }
        }
    });
}

// 7. YENİ HARCAMA EKLEME
if (expenseForm) {
    expenseForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const token = localStorage.getItem("token");
        const title = expenseTitle.value;
        const amount = parseFloat(expenseAmount.value);
        const category = expenseCategory.value;
        const date = expenseDate.value;

        try {
            const response = await fetch(`${API_URL}/expenses?title=${encodeURIComponent(title)}&amount=${amount}&category=${encodeURIComponent(category)}&date=${encodeURIComponent(date)}`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });

            if (response.ok) {
                expenseForm.reset();
                if (expenseDate) expenseDate.value = new Date().toISOString().split('T')[0];
                loadExpenses();
            } else {
                alert("Failed to save expense.");
            }
        } catch (error) {
            console.error("Add expense error:", error);
        }
    });
}

// 8. HARCAMA SİLME
async function deleteExpense(expenseId) {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
        const response = await fetch(`${API_URL}/expenses/${expenseId}`, {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        });

        if (response.ok) {
            loadExpenses();
        } else {
            alert("Failed to delete expense.");
        }
    } catch (error) {
        console.error("Delete expense error:", error);
    }
}

// 9. YAPAY ZEKA TAVSİYESİ (GEMINI)
if (getAiAdviceBtn) {
    getAiAdviceBtn.addEventListener("click", async () => {
        const token = localStorage.getItem("token");
        if (!token) return;

        aiAdviceResult.innerHTML = "<p>Analyzing your spending...</p>";

        try {
            const response = await fetch(`${API_URL}/ai/advice`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` }
            });

            const data = await response.json();

            if (response.ok) {
                aiAdviceResult.innerHTML = `<p>${data.ai_advice || data.advice}</p>`;
            } else {
                aiAdviceResult.innerHTML = `<p>Error: ${data.detail || "Could not fetch AI advice."}</p>`;
            }
        } catch (error) {
            console.error("AI Advice error:", error);
            aiAdviceResult.innerHTML = "<p>Connection error with AI service.</p>";
        }
    });
}

checkAuth();