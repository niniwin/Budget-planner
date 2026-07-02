  let currentPage = 1;
    
const editIcon = `
    <svg class="action-icon" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M15.502 1.94a.5.5 0 0 1 0 .706l-1.043 1.043-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293z"/>
        <path d="M13.752 4.396l-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.815z"/>
        <path d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5z"/>
    </svg>
`;

const deleteIcon = `
    <svg class="action-icon" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14m0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16"/>
        <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708"/>
    </svg>
`;

const saveIcon = `
    <svg class="action-icon" viewBox="0 0 16 16" aria-hidden="true">
        <path d="M2 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V2.5L13.5 1zm11 1.5V6H3V2h9.5zM3 14v-5h10v5z"/>
    </svg>
`;

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
                    ${editIcon}
                </button>
            </td>
            <td class="text-center">
                <button type="button" class="delete-btn" onclick="this.closest('tr').remove()">
                    ${deleteIcon}
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
    button.innerHTML = saveIcon;

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
        button.innerHTML = editIcon;

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
                            ${editIcon}
                            </button>
                        </td>
                        <td class="text-center">
                            <button type="button" class="delete-btn" onclick="deleteRow(this)">
                            ${deleteIcon}
                            </button>
                        </td>
                    </tr>
                 `;

                
                   tableBody.insertAdjacentHTML("beforeend", row);
            });

            renderPagination(response); // NEW
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
    
  


