  let currentPage = 1;
    
 function addRow(type) {
    const table = document.getElementById("transactionsTable");

    const row = `
        <tr>
            <td>
                <select name="type[]" class="form-control">
                    <option value="income" ${type === 'income' ? 'selected' : ''}>Income</option>
                    <option value="expense" ${type === 'expense' ? 'selected' : ''}>Expense</option>
                </select>
            </td>
            <td>
                <input type="date" name="date[]" class="form-control" required>
            </td>
            <td>
                <input type="text" name="description[]" class="form-control" required>
            </td>
            <td>
                <input type="number" name="amount[]" class="form-control" step="0.01" required>
            </td>
            <td class="text-center">
                <button type="button" class="update-btn" disabled>
                    <i class="bi bi-pencil-square"></i>
                </button>
            </td>
            <td class="text-center">
                <button type="button" class="delete-btn" onclick="this.closest('tr').remove()">
                    <i class="bi bi-x-circle"></i>
                </button>
            </td>
        </tr>
    `;

    table.insertAdjacentHTML("beforeend", row);
}
 function deleteRow(button) {
    let row = button.closest("tr");
    let id = row.dataset.id;
  

    if (!id) {
        row.remove();
        return;
    }

    if (!confirm("Delete this item?")) return;

    fetch(`/delete/${id}`, { method: 'DELETE' })
        .then(res => {
            if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
            row.remove();
        })
        .catch(err => {
            console.error(err);
            alert("Delete failed");
        });
}
function editRow(button){
    let row = button.closest("tr");
    let inputs = row.querySelectorAll("input");

    inputs.forEach(input => input.disabled = false);

    // change icon
    button.innerHTML = '<i class="bi bi-save"></i>';

    // change behavior
    button.onclick = function () {
        saveRow(row, button);
    };
}

function saveRow(row, button) {
    let id = row.dataset.id;
    let inputs = row.querySelectorAll("input");

    let data = {
        date: inputs[0].value,
        description: inputs[1].value,
        amount: inputs[2].value
    };

    fetch(`/update/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(() => {
        // disable again
        inputs.forEach(input => input.disabled = true);

        // change back to edit icon
        button.innerHTML = '<i class="bi bi-pencil-square"></i>';

        // restore edit behavior
        button.onclick = function () {
            editRow(button);
        };
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const menuButton = document.querySelector(".mobile-menu-btn");
    const menuClose = document.querySelector(".mobile-menu-close");
    const menuBackdrop = document.querySelector(".mobile-menu-backdrop");
    const sidebarLinks = document.querySelectorAll(".budget-sidebar .sidebar-link");

    function openMobileMenu() {
        document.body.classList.add("mobile-menu-open");
        menuButton?.setAttribute("aria-expanded", "true");
    }

    function closeMobileMenu() {
        document.body.classList.remove("mobile-menu-open");
        menuButton?.setAttribute("aria-expanded", "false");
    }

    menuButton?.addEventListener("click", openMobileMenu);
    menuClose?.addEventListener("click", closeMobileMenu);
    menuBackdrop?.addEventListener("click", closeMobileMenu);
    sidebarLinks.forEach(link => link.addEventListener("click", closeMobileMenu));
    // Handle ADD transaction form
   const addForm = document.querySelector("form[action='/add-transaction']");

    if (addForm) {
    addForm.addEventListener("submit", function(e){
        e.preventDefault();

        let formData = new FormData(this);
        let btn = this.querySelector("button[type='submit']");
        btn.disabled = true;

        fetch('/add-transaction', {
            method: 'POST',
            body: formData
        })
        .then(() => {
            window.location.reload();
        })
        .finally(() => {
            btn.disabled = false;
        });
    });
}
});



function loadTransactions(page = 1) {

    currentPage = page;
    // clear tables first
    const tableBody = document.getElementById("transactionsTable");
       tableBody.innerHTML = "";
 

    const startDate = document.querySelector("input[name='start_date']")?.value || "";
    const endDate = document.querySelector("input[name='end_date']")?.value || "";

    let url = `/transactions?page=${page}`;

    if (startDate && endDate) {
    url += `&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`;
    }

    console.log("Fetching URL:", url);

    fetch(url)
        .then(res => res.json())
        .then(response => {

            const transactions = response.data;

            transactions.forEach(t => {

               const row = `
                    <tr data-id="${t.id}">
                     <td>
                            <select class="form-control" disabled>
                                <option value="income" ${t.type === 'income' ? 'selected' : ''}>Income</option>
                                <option value="expense" ${t.type === 'expense' ? 'selected' : ''}>Expense</option>
                            </select>
                        </td>
                    <td><input type="date" value="${t.date.slice(0,10)}" class="form-control" disabled></td>
                    <td><input type="text" value="${t.description}" class="form-control" disabled></td>
                    <td><input type="number" value="${t.amount}" class="form-control" disabled></td>
                    <td>       
                            <button type="button" class="update-btn" onclick="editRow(this)">
                            <i class="bi bi-pencil-square"></i>
                            </button>
                        </td>
                        <td class="text-center">
                            <button type="button" class="delete-btn" onclick="deleteRow(this)">
                            <i class="bi bi-x-circle"></i>
                            </button>
                        </td>
                    </tr>
                 `;

                
                   tableBody.insertAdjacentHTML("beforeend", row);
            });

            renderPagination(response); // âœ… NEW
        })
        .catch(error => {
            console.error("Error loading transactions:", error);
        });
}

function downloadDailySummary() {
    const rows = [];
    const table = document.querySelector(".transaction-table");

    if (!table) return;

    table.querySelectorAll("tr").forEach(row => {
        const cells = Array.from(row.querySelectorAll("th, td"))
            .map(cell => `"${cell.innerText.trim()}"`);

        rows.push(cells.join(","));
    });

    const csv = rows.join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "daily-summary.csv";
    link.click();

    URL.revokeObjectURL(url);
}

function renderPagination(data) {
    const container = document.getElementById("pagination");
    if (!container) return;

    const prevPage = Math.max(1, data.current_page - 1);
    const nextPage = Math.min(data.total_pages, data.current_page + 1);

    container.innerHTML = `
        <button
            type="button"
            onclick="loadTransactions(${prevPage})"
            ${data.current_page === 1 ? 'disabled' : ''}>
            Prev
        </button>

        <span class="mx-3">
            Page ${data.current_page} of ${data.total_pages}
        </span>

        <button
            type="button"
            onclick="loadTransactions(${nextPage})"
            ${data.current_page === data.total_pages ? 'disabled' : ''}>
            Next
        </button>
    `;
}
    
  


