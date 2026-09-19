let currentCell = null;
let originalState = null;


/* ================= OPEN PREVIEW ================= */

function openPreview(el) {

    currentCell = el;

    // 🔒 zapamiętaj stan przed edycją

    originalState = {

        img: el.dataset.img || '',

        desc: el.dataset.desc || '',

        activityname:
            el.dataset.activityname || '',

        start:
            el.dataset.start || '',

        end:
            el.dataset.end || '',

        day:
            el.dataset.day || '',

        personId: el.dataset.personId || ''

    };


    document.getElementById('p-img').src =
        originalState.img;

    document.getElementById('p-start').value =
        originalState.start;

    document.getElementById('p-end').value =
        originalState.end;

    document.getElementById('p-desc-input').value =
        originalState.desc;


    // 📅 ustaw aktualny dzień

    document.getElementById('p-day').value =
        originalState.day;

    // 👤 ustaw aktualną osobę

    document.getElementById('p-person').value =
        el.dataset.personId || '';

    // 🖼️ ustaw aktywność

    const select =
        document.getElementById(
            'p-activity-select'
        );

    select.value =
        originalState.activityname;


    document
        .getElementById('preview')
        .classList.add('active');
}


/* ================= CLOSE PREVIEW ================= */

function closePreview() {

    if (currentCell && originalState) {

        // 🔙 przywróć dataset

        currentCell.dataset.img =
            originalState.img;

        currentCell.dataset.desc =
            originalState.desc;

        currentCell.dataset.activityname =
            originalState.activityname;

        currentCell.dataset.start =
            originalState.start;

        currentCell.dataset.end =
            originalState.end;

        currentCell.dataset.day =
            originalState.day;


        // 🔙 przywróć obrazek

        let tileImg =
            currentCell.querySelector(
                '.tile-img'
            );


        if (originalState.img) {

            if (!tileImg) {

                tileImg =
                    document.createElement(
                        'img'
                    );

                tileImg.className =
                    'tile-img';

                currentCell.prepend(
                    tileImg
                );
            }

            tileImg.src =
                originalState.img;

        } else if (tileImg) {

            tileImg.remove();

        }


        // 🔙 przywróć opis

        const overlay =
            currentCell.querySelector(
                '.tile-overlay'
            );

        if (overlay) {

            overlay.textContent =
                originalState.desc;

        }

    }


    document
        .getElementById('preview')
        .classList.remove('active');


    currentCell = null;
    originalState = null;
}


/* ================= ACTIVITY CHANGE ================= */

document
    .getElementById(
        'p-activity-select'
    )
    .addEventListener(
        'change',
        e => {

            const selected =
                e.target.selectedOptions[0];

            if (!selected) return;


            const imgUrl =
                selected.dataset.picture || '';


            // 🖼️ preview

            const previewImg =
                document.getElementById(
                    'p-img'
                );

            previewImg.src =
                imgUrl;


            // 🧠 zapamiętaj do zapisu

            if (currentCell) {

                currentCell.dataset.img =
                    imgUrl;


                let tileImg =
                    currentCell.querySelector(
                        '.tile-img'
                    );


                if (!tileImg) {

                    tileImg =
                        document.createElement(
                            'img'
                        );

                    tileImg.className =
                        'tile-img';

                    currentCell.prepend(
                        tileImg
                    );

                }

                tileImg.src =
                    imgUrl;

            }

        }
    );


/* ================= SAVE ================= */

function saveEdit() {

    if (!currentCell) return;


    const activityId =
        currentCell.dataset.activityId;


    const formData =
        new FormData();


    formData.append(
        "start",
        document.getElementById(
            'p-start'
        ).value
    );


    formData.append(
        "end",
        document.getElementById(
            'p-end'
        ).value
    );


    formData.append(
        "description",
        document.getElementById(
            'p-desc-input'
        ).value
    );


    formData.append(
        "activityname",
        document
            .getElementById(
                'p-activity-select'
            )
            .value
    );

    formData.append(
        "person_id",
        document.getElementById('p-person').value
    );


    // 📅 NOWY DZIEŃ

    formData.append(
        "day",
        document.getElementById(
            'p-day'
        ).value
    );


    fetch(
        `/live/statusall/edit/${activityId}`,
        {
            method: "PUT",
            body: formData
        }
    )

    .then(async r => {

        const text =
            await r.text();


        if (!r.ok) {

            console.error(
                "STATUS:",
                r.status
            );

            console.error(
                "RESPONSE:",
                text
            );


            let message = text;


            // Próba odczytania JSON
            try {

                const data =
                    JSON.parse(text);

                if (
                    data.errors &&
                    Array.isArray(data.errors)
                ) {

                    message =
                        data.errors.join("\n");

                } else if (
                    data.detail
                ) {

                    message =
                        data.detail;

                }

            } catch (e) {
                // odpowiedź nie była JSON
            }


            throw new Error(
                message ||
                "Błąd zapisu"
            );
        }


        return text;

    })

    .then(() => {

        closePreview();

        location.reload();

    })

    .catch(err => {

        showErrorToast(
            err.message
        );

    });

}


/* ================= AUTO REFRESH ================= */

setInterval(() => {

    const previewOpen =
        document
            .getElementById('preview')
            .classList
            .contains('active');

    const createPreviewOpen =
        document
            .getElementById('create-preview')
            .classList
            .contains('active');


    /*
     * NIE odświeżaj strony, jeżeli:
     * - otwarte jest okno edycji
     * LUB
     * - otwarte jest okno tworzenia aktywności
     *
     * Dzięki temu wpisywane dane nie znikną
     * po 30 sekundach.
     */

    if (
        !document.hidden &&
        !previewOpen &&
        !createPreviewOpen
    ) {

        location.reload();

    }

}, 30000);


/* ================= ERROR TOAST ================= */

function showErrorToast(message) {

    const toast =
        document.getElementById(
            "toast"
        );

    const text =
        document.getElementById(
            "toast-text"
        );


    text.innerText =
        "❌ " + message;


    toast.style.display =
        "block";


    setTimeout(() => {

        toast.style.opacity =
            "0";


        setTimeout(() => {

            toast.style.display =
                "none";

            toast.style.opacity =
                "1";

        }, 300);

    }, 4500);

}


/* ================= DELETE ================= */

function deleteActivity() {

    if (!currentCell) return;


    const activityId =
        currentCell.dataset.activityId;


    if (!activityId) return;


    showDeleteConfirm(
        function() {

            fetch(
                `/activities/delete/${activityId}`,
                {
                    method: "POST"
                }
            )

            .then(r => {

                if (!r.ok) {

                    throw new Error(
                        "Nie udało się usunąć aktywności"
                    );

                }


                closePreview();

                location.reload();

            })

            .catch(err =>

                showErrorToast(
                    err.message
                )

            );

        },

        "Usuń aktywność?",

        "Czy na pewno chcesz usunąć tę aktywność?"
    );

}


/* ================= CHANGE DAY ================= */

const currentDay = window.currentDay;


function changeDay(step) {

    let newDay =
        currentDay + step;


    if (newDay < 1)
        newDay = 7;


    if (newDay > 7)
        newDay = 1;


    window.location.href =
        `/live/liveall/${newDay}`;

}


/* ================= DATE TIME LIVE ================= */

function updateDateTime() {

    const el =
        document.getElementById(
            'datetime'
        );


    const now =
        new Date();


    const days = [

        'Niedziela',
        'Poniedziałek',
        'Wtorek',
        'Środa',
        'Czwartek',
        'Piątek',
        'Sobota'

    ];


    const day =
        days[now.getDay()];


    const time =
        now.toLocaleTimeString(
            'pl-PL',
            {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            }
        );


    el.textContent =
        `${time}`;

}


/* ================= CREATE ACTIVITY FOR EMPTY CELL ================= */

function createActivityForPerson(personId) {

    // Ustaw aktualnie oglądany dzień
    document.getElementById('c-day').value =
        currentDay.toString();

    // Ustaw osobę z klikniętej kolumny
    document.getElementById('c-person').value =
        personId.toString();

    // Wyczyść formularz
    document.getElementById('c-start').value = '';
    document.getElementById('c-end').value = '';
    document.getElementById('c-activity').value = '';
    document.getElementById('c-desc').value = '';

    // Wyczyść obrazek
    const img = document.getElementById('c-img');

    img.src = '';
    img.style.display = 'none';

    // Pokaż modal
    document
        .getElementById('create-preview')
        .classList.add('active');
}


/* ================= CREATE ACTIVITY ================= */

function createActivity() {

    // Domyślnie ustaw aktualnie oglądany dzień
    document.getElementById('c-day').value =
        currentDay.toString();

    // Wyczyść formularz
    document.getElementById('c-start').value = '';
    document.getElementById('c-end').value = '';
    document.getElementById('c-person').value = '';
    document.getElementById('c-activity').value = '';
    document.getElementById('c-desc').value = '';

    // Wyczyść obrazek
    const img = document.getElementById('c-img');

    img.src = '';
    img.style.display = 'none';

    // Pokaż popup
    document
        .getElementById('create-preview')
        .classList.add('active');
}


/* ================= CLOSE CREATE ================= */

function closeCreatePreview() {

    document
        .getElementById('create-preview')
        .classList.remove('active');
}


/* ================= CREATE ACTIVITY IMAGE ================= */

document
    .getElementById('c-activity')
    .addEventListener('change', function () {

        const selected =
            this.selectedOptions[0];

        const img =
            document.getElementById('c-img');

        const imgUrl =
            selected?.dataset.picture || '';

        if (imgUrl) {

            img.src = imgUrl;
            img.style.display = 'block';

        } else {

            img.src = '';
            img.style.display = 'none';

        }

    });


/* ================= SAVE NEW ACTIVITY ================= */

/* ================= SAVE NEW ACTIVITY ================= */

function saveCreateActivity() {

    const start =
        document.getElementById('c-start').value;

    const end =
        document.getElementById('c-end').value;

    const day =
        document.getElementById('c-day').value;

    const person =
        document.getElementById('c-person').value;

    const activity =
        document.getElementById('c-activity').value;

    const description =
        document.getElementById('c-desc').value;


    // Podstawowa walidacja po stronie przeglądarki

    if (!start) {

        showErrorToast(
            'Podaj godzinę rozpoczęcia.'
        );

        return;

    }


    if (!end) {

        showErrorToast(
            'Podaj godzinę zakończenia.'
        );

        return;

    }


    if (!person) {

        showErrorToast(
            'Wybierz osobę.'
        );

        return;

    }


    if (!activity) {

        showErrorToast(
            'Wybierz aktywność.'
        );

        return;

    }


    const formData =
        new FormData();


    formData.append(
        'start',
        start
    );

    formData.append(
        'end',
        end
    );

    formData.append(
        'day_of_week',
        day
    );

    formData.append(
        'description',
        description
    );

    formData.append(
        'person_id',
        person
    );

    formData.append(
        'activity_name',
        activity
    );


    fetch(
        '/activities/add',
        {
            method: 'POST',
            body: formData
        }
    )

    .then(async response => {

        /*
         * SUKCES
         *
         * Backend zwraca RedirectResponse.
         */

        if (response.redirected) {

            window.location.href =
                response.url;

            return;

        }


        const text =
            await response.text();


        /*
         * BŁĄD
         *
         * Backend zwraca activity_add.html
         * z listą konkretnych błędów.
         */

        if (!response.ok) {

            try {

                const parser =
                    new DOMParser();

                const doc =
                    parser.parseFromString(
                        text,
                        'text/html'
                    );


                const errorBox =
                    doc.querySelector('.errors');


                if (errorBox) {

                    const errors =
                        Array.from(
                            errorBox.querySelectorAll('li')
                        )
                        .map(li => li.textContent.trim())
                        .filter(Boolean);


                    if (errors.length > 0) {

                        throw new Error(
                            errors.join('\n')
                        );

                    }

                }

            } catch (e) {

                /*
                 * Jeżeli udało się wyciągnąć
                 * konkretny komunikat, przepuszczamy go dalej.
                 */

                if (
                    e instanceof Error &&
                    e.message &&
                    !e.message.includes('DOMParser')
                ) {

                    throw e;

                }

            }


            throw new Error(
                'Nie udało się utworzyć aktywności.'
            );

        }


        /*
         * Nieoczekiwana odpowiedź bez przekierowania.
         */

        throw new Error(
            'Nie udało się utworzyć aktywności. Sprawdź dane formularza.'
        );

    })

    .catch(error => {

        showErrorToast(
            error.message
        );

    });

}



updateDateTime();


setInterval(
    updateDateTime,
    1000
);
