let touchStartX = 0;

document.addEventListener('touchstart', function(event) {
    touchStartX = event.changedTouches[0].screenX;
}, { passive: true });

document.addEventListener('touchend', function(event) {

    const touchEndX =
        event.changedTouches[0].screenX;

    const diff =
        touchEndX - touchStartX;

    if (Math.abs(diff) < 80) {
        return;
    }

    const params =
        new URLSearchParams(window.location.search);

    let weekOffset =
        parseInt(params.get('week_offset') || '0', 10);

    if (diff < 0) {
        weekOffset++;
    } else {
        weekOffset--;
    }

    window.location.href =
        '?week_offset=' + weekOffset;

}, { passive: true });
