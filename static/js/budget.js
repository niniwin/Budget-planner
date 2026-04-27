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
            loadTransactions(currentPage);
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

    // ✅ 0. Set default month (ADD THIS PART HERE)
    const monthInput = document.getElementById("monthPicker");
    if (monthInput && !monthInput.value) {
        const now = new Date();
        monthInput.value = now.toISOString().slice(0, 7);
    }

    // ✅ 1. Load data ONLY ONCE when page loads
    loadTransactions();

    // ✅ 2. Filter form (ADD THIS — important)
    const filterForm = document.querySelector(".row.g-3");
    if (filterForm) {
        filterForm.addEventListener("submit", function(e) {
            e.preventDefault();
            loadTransactions(1); // reset to page 1 when filtering
        });
    }

    // ✅ 3. Handle ADD transaction form (your existing code)
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
            this.reset();
            loadTransactions();
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
 

    const month = document.getElementById("monthPicker")?.value || "";
     console.log("Selected month:", month);

    let url = `/transactions?page=${page}`;
    if (month) {
        url += `&month=${month}`;
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

            renderPagination(response); // ✅ NEW
        })
        .catch(error => {
            console.error("Error loading transactions:", error);
        });
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
    
  
