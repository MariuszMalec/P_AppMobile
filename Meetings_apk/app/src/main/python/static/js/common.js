// =========================================================
// WSPÓLNY KOMUNIKAT
// =========================================================

function showMessage(text) {

    const messageBox =
        document.getElementById('message');

    if (!messageBox) {
        console.error(
            'Element #message nie został znaleziony.'
        );
        return;
    }

    messageBox.textContent = text;

    messageBox.classList.add('show');

    setTimeout(function() {

        messageBox.classList.remove('show');

    }, 2500);
}


// =========================================================
// ESCAPOWANIE HTML
// =========================================================

function escapeHtml(value) {

    const div = document.createElement('div');

    div.textContent = value ?? '';

    return div.innerHTML;
}


// =========================================================
// CUSTOM DIALOG SYSTEM
// =========================================================

let customDialogResolver = null;


function showDialog(
    message,
    type = "info",
    title = null
) {
    const overlay =
        document.getElementById(
            "custom-dialog-overlay"
        );

    const dialog =
        document.getElementById(
            "custom-dialog"
        );

    const icon =
        document.getElementById(
            "custom-dialog-icon"
        );

    const titleElement =
        document.getElementById(
            "custom-dialog-title"
        );

    const messageElement =
        document.getElementById(
            "custom-dialog-message"
        );

    const buttons =
        document.getElementById(
            "custom-dialog-buttons"
        );

    if (!overlay || !dialog) {
        console.error(
            "Custom dialog nie został znaleziony."
        );

        return;
    }

    dialog.classList.remove(
        "success",
        "info",
        "warning",
        "error"
    );

    dialog.classList.add(type);

    const settings = {
        success: {
            icon: "✓",
            title: "Gotowe"
        },

        info: {
            icon: "ℹ",
            title: "Informacja"
        },

        warning: {
            icon: "!",
            title: "Uwaga"
        },

        error: {
            icon: "×",
            title: "Błąd"
        }
    };

    const current =
        settings[type] ||
        settings.info;

    icon.textContent =
        current.icon;

    titleElement.textContent =
        title || current.title;

    messageElement.textContent =
        message;

    buttons.innerHTML = "";

    const okButton =
        document.createElement("button");

    okButton.type = "button";

    okButton.className =
        "custom-dialog-button confirm";

    okButton.textContent =
        "OK";

    okButton.addEventListener(
        "click",
        () => {
            closeDialog();
        }
    );

    buttons.appendChild(
        okButton
    );

    overlay.classList.add(
        "active"
    );

    setTimeout(
        () => okButton.focus(),
        0
    );
}


function showConfirmDialog(
    message,
    options = {}
) {
    return new Promise(resolve => {

        const overlay =
            document.getElementById(
                "custom-dialog-overlay"
            );

        const dialog =
            document.getElementById(
                "custom-dialog"
            );

        const icon =
            document.getElementById(
                "custom-dialog-icon"
            );

        const titleElement =
            document.getElementById(
                "custom-dialog-title"
            );

        const messageElement =
            document.getElementById(
                "custom-dialog-message"
            );

        const buttons =
            document.getElementById(
                "custom-dialog-buttons"
            );

        if (!overlay || !dialog) {
            console.error(
                "Custom dialog nie został znaleziony."
            );

            resolve(false);

            return;
        }

        if (customDialogResolver) {
            customDialogResolver(false);
        }

        customDialogResolver =
            resolve;

        dialog.classList.remove(
            "success",
            "info",
            "warning",
            "error"
        );

        dialog.classList.add(
            options.type || "warning"
        );

        icon.textContent =
            options.icon || "!";

        titleElement.textContent =
            options.title || "Potwierdzenie";

        messageElement.textContent =
            message;

        buttons.innerHTML = "";

        const cancelButton =
            document.createElement("button");

        cancelButton.type = "button";

        cancelButton.className =
            "custom-dialog-button cancel";

        cancelButton.textContent =
            options.cancelText || "Anuluj";

        cancelButton.addEventListener(
            "click",
            () => {
                finishDialog(false);
            }
        );

        const confirmButton =
            document.createElement("button");

        confirmButton.type = "button";

        confirmButton.className =
            "custom-dialog-button " +
            (
                options.danger
                    ? "danger"
                    : "confirm"
            );

        confirmButton.textContent =
            options.confirmText || "OK";

        confirmButton.addEventListener(
            "click",
            () => {
                finishDialog(true);
            }
        );

        buttons.appendChild(
            cancelButton
        );

        buttons.appendChild(
            confirmButton
        );

        overlay.classList.add(
            "active"
        );

        setTimeout(
            () => confirmButton.focus(),
            0
        );
    });
}


function finishDialog(result) {

    const resolver =
        customDialogResolver;

    customDialogResolver =
        null;

    closeDialog();

    if (resolver) {
        resolver(result);
    }
}


function closeDialog() {

    const overlay =
        document.getElementById(
            "custom-dialog-overlay"
        );

    if (!overlay) {
        return;
    }

    overlay.classList.remove(
        "active"
    );
}


document.addEventListener(
    "keydown",
    event => {

        if (event.key !== "Escape") {
            return;
        }

        const overlay =
            document.getElementById(
                "custom-dialog-overlay"
            );

        if (
            !overlay ||
            !overlay.classList.contains(
                "active"
            )
        ) {
            return;
        }

        if (customDialogResolver) {
            finishDialog(false);
        } else {
            closeDialog();
        }
    }
);