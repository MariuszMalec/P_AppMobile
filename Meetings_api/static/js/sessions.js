let touchStartX = 0;
let touchStartY = 0;
let touchIgnore = false;

document.addEventListener('touchstart', function(event) {
    const t = event.changedTouches[0];
    touchStartX = t.screenX;
    touchStartY = t.screenY;
    touchIgnore = !!event.target.closest(
        '.table-wrap, input, select, textarea'
    );
}, { passive: true });

document.addEventListener('touchend', function(event) {

    if (touchIgnore) {
        return;
    }

    if (document.querySelector(
        '.preview-bg.active, .custom-dialog-overlay.active'
    )) {
        return;
    }

    const t = event.changedTouches[0];
    const dx = t.screenX - touchStartX;
    const dy = t.screenY - touchStartY;

    if (Math.abs(dx) < 80 || Math.abs(dx) < Math.abs(dy) * 2) {
        return;
    }

    const params =
        new URLSearchParams(window.location.search);

    let weekOffset =
        parseInt(params.get('week_offset') || '0', 10);

    weekOffset += dx < 0 ? 1 : -1;

    window.location.href =
        '?week_offset=' + weekOffset;

}, { passive: true });


// =========================================================
// PODŚWIETLENIE DZISIEJSZEJ KOLUMNY
// =========================================================

function highlightToday() {

    const params =
        new URLSearchParams(window.location.search);

    const offset =
        parseInt(params.get('week_offset') || '0', 10);

    // dzisiaj widać tylko w bieżącym tygodniu
    if (offset !== 0) {
        return;
    }

    const jsDay = new Date().getDay();
    const day = jsDay === 0 ? 7 : jsDay;

    document
        .querySelectorAll(
            'th.day-header[data-day="' + day + '"], ' +
            '.table-wrap td[data-day="' + day + '"]'
        )
        .forEach(el => el.classList.add('today-col'));

    const card =
        document.querySelectorAll(
            '#mobile-week-view .mobile-day-card'
        )[day - 1];

    if (card) {
        card.classList.add('today-card');
    }
}

document.addEventListener(
    'DOMContentLoaded',
    highlightToday
);


// =========================================================
// DOPASOWANIE WYSOKOŚCI TABELI DO EKRANU
// =========================================================

function fitTableHeight() {

    const wrap = document.querySelector('.table-wrap');

    if (!wrap || wrap.offsetParent === null) {
        return;
    }

    const vh = window.visualViewport
        ? window.visualViewport.height
        : window.innerHeight;

    const top = wrap.getBoundingClientRect().top + window.scrollY;

    wrap.style.maxHeight =
        Math.max(240, vh - top - 8) + 'px';
}

window.addEventListener('load', fitTableHeight);
window.addEventListener('resize', fitTableHeight);
window.addEventListener('orientationchange', fitTableHeight);

document.addEventListener('click', function(e) {
    if (e.target.closest('#toggle-mobile-view')) {
        setTimeout(fitTableHeight, 50);
    }
});
