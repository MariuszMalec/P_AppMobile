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