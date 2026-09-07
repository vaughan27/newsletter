document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupYearNavigation();

        setupSearch();

    }
);


/* --------------------------------
   YEAR NAVIGATION
-------------------------------- */

function setupYearNavigation() {

    const buttons =
        document.querySelectorAll(
            ".year-button"
        );


    const sections =
        document.querySelectorAll(
            ".year-section"
        );


    buttons.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const year =
                    button.dataset.year;


                buttons.forEach(
                    item => {

                        item.classList.remove(
                            "active"
                        );

                    }
                );


                button.classList.add(
                    "active"
                );


                sections.forEach(
                    section => {

                        if (
                            year === "all"
                            ||
                            section.dataset.yearSection === year
                        ) {

                            section.style.display =
                                "";

                        } else {

                            section.style.display =
                                "none";

                        }

                    }
                );

            }
        );

    });

}


/* --------------------------------
   SEARCH
-------------------------------- */

function setupSearch() {

    const input =
        document.getElementById(
            "searchInput"
        );


    if (!input) {
        return;
    }


    const archive =
        document.getElementById(
            "archive"
        );


    const searchResults =
        document.getElementById(
            "searchResults"
        );


    let timer;


    input.addEventListener(
        "input",
        () => {

            clearTimeout(
                timer
            );


            const query =
                input.value.trim();


            if (!query) {

                searchResults.classList.add(
                    "hidden"
                );

                archive.classList.remove(
                    "hidden"
                );

                return;

            }


            timer =
                setTimeout(
                    () => {

                        performSearch(
                            query
                        );

                    },
                    250
                );

        }
    );


    async function performSearch(
        query
    ) {

        searchResults.innerHTML = `
            <div class="search-loading">
                Searching...
            </div>
        `;


        searchResults.classList.remove(
            "hidden"
        );


        archive.classList.add(
            "hidden"
        );


        try {

            const response =
                await fetch(
                    `/api/search?q=${encodeURIComponent(
                        query
                    )}`
                );


            const results =
                await response.json();


            renderSearchResults(
                results,
                query
            );


        } catch (error) {

            console.error(
                error
            );


            searchResults.innerHTML = `
                <div class="empty-state">
                    <h2>
                        Search failed
                    </h2>

                    <p>
                        Please try again.
                    </p>
                </div>
            `;

        }

    }


    function renderSearchResults(
        results,
        query
    ) {

        if (
            results.length === 0
        ) {

            searchResults.innerHTML = `
                <div class="empty-state">

                    <h2>
                        No results
                    </h2>

                    <p>
                        Nothing matched
                        "${escapeHtml(query)}".
                    </p>

                </div>
            `;

            return;

        }


        searchResults.innerHTML = `

            <div class="search-heading">

                <h2>
                    Search results
                </h2>

                <span>
                    ${results.length}
                    result${
                        results.length === 1
                            ? ""
                            : "s"
                    }
                </span>

            </div>


            <div class="search-result-list">

                ${results.map(
                    result => `

                    <a
                        class="search-result"
                        href="${result.url}"
                    >

                        ${
                            result.cover

                            ? `
                                <img
                                    src="${result.cover}"
                                    alt=""
                                >
                              `

                            : ""
                        }


                        <div>

                            <div
                                class="search-result-date"
                            >
                                ${result.date}
                            </div>


                            <h3>
                                ${escapeHtml(
                                    result.title
                                )}
                            </h3>


                            ${
                                result.description

                                ? `
                                    <p>
                                        ${escapeHtml(
                                            result.description
                                        )}
                                    </p>
                                  `

                                : ""
                            }

                        </div>

                    </a>

                `
                ).join("")}

            </div>

        `;

    }

}


/* --------------------------------
   ESCAPE HTML
-------------------------------- */

function escapeHtml(
    value
) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        value;


    return div.innerHTML;

}