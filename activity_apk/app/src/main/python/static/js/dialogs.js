/* =========================================================
   WSPÓLNE DIALOGI
   ========================================================= */

let deleteConfirmCallback = null;


/* =========================================================
   UTWORZENIE MODALA
   ========================================================= */

function createDeleteConfirm() {

    if (document.getElementById("delete-confirm")) {
        return;
    }

    const modal = document.createElement("div");

    modal.id = "delete-confirm";
    modal.className = "delete-confirm-bg";

    modal.innerHTML = `
        <div
            class="delete-confirm-card"
            onclick="event.stopPropagation()"
        >

            <div class="delete-confirm-icon">
                🗑
            </div>

            <div class="delete-confirm-title">
                Usuń element?
            </div>

            <div class="delete-confirm-text">
                Czy na pewno chcesz usunąć ten element?
                <br>
                Tej operacji nie można cofnąć.
            </div>

            <div class="delete-confirm-buttons">

                <button
                    type="button"
                    class="delete-cancel"
                    onclick="closeDeleteConfirm()"
                >
                    Anuluj
                </button>

                <button
                    type="button"
                    class="delete-confirm"
                    onclick="confirmDelete()"
                >
                    🗑 Usuń
                </button>

            </div>

        </div>
    `;

    modal.addEventListener(
        "click",
        closeDeleteConfirm
    );

    document.body.appendChild(modal);
}


/* =========================================================
   POKAZANIE POTWIERDZENIA
   ========================================================= */

function showDeleteConfirm(
    callback,
    title = "Usuń element?",
    message = "Czy na pewno chcesz usunąć ten element?"
) {

    createDeleteConfirm();

    deleteConfirmCallback = callback;

    const modal =
        document.getElementById("delete-confirm");

    const titleElement =
        modal.querySelector(".delete-confirm-title");

    const textElement =
        modal.querySelector(".delete-confirm-text");

    titleElement.textContent = title;

    textElement.innerHTML =
        message +
        "<br>Tej operacji nie można cofnąć.";

    modal.classList.add("active");
}


/* =========================================================
   ZAMKNIĘCIE
   ========================================================= */

function closeDeleteConfirm() {

    const modal =
        document.getElementById("delete-confirm");

    if (!modal) {
        return;
    }

    modal.classList.remove("active");

    deleteConfirmCallback = null;
}


/* =========================================================
   POTWIERDZENIE USUNIĘCIA
   ========================================================= */

function confirmDelete() {

    if (
        typeof deleteConfirmCallback !==
        "function"
    ) {
        closeDeleteConfirm();
        return;
    }

    const callback =
        deleteConfirmCallback;

    closeDeleteConfirm();

    callback();
}


/* =========================================================
   ESC
   ========================================================= */

document.addEventListener(
    "keydown",
    function(event) {

        if (event.key === "Escape") {
            closeDeleteConfirm();
        }

    }
);


/* =========================================================
   START
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        createDeleteConfirm();

    }
);
