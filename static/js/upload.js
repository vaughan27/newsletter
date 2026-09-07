document.addEventListener(
    "DOMContentLoaded",
    () => {

        const pdfInput =
            document.getElementById(
                "pdf"
            );


        const titleInput =
            document.getElementById(
                "title"
            );


        const dateInput =
            document.getElementById(
                "publication_date"
            );


        if (!pdfInput) {
            return;
        }


        pdfInput.addEventListener(
            "change",
            () => {

                const file =
                    pdfInput.files[0];


                if (!file) {
                    return;
                }


                /*
                 * Automatically suggest
                 * a title from the filename.
                 */

                if (
                    !titleInput.value
                ) {

                    titleInput.value =
                        file.name
                            .replace(
                                /\.pdf$/i,
                                ""
                            )
                            .replace(
                                /[-_]/g,
                                " "
                            );

                }


                /*
                 * Try to determine date
                 * from filename.
                 *
                 * Example:
                 * 2026-08-newsletter.pdf
                 */

                if (
                    !dateInput.value
                ) {

                    const match =
                        file.name.match(
                            /(\d{4})[-_](\d{2})(?:[-_](\d{2}))?/
                        );


                    if (match) {

                        const year =
                            match[1];


                        const month =
                            match[2];


                        const day =
                            match[3]
                            || "01";


                        dateInput.value =
                            `${year}-${month}-${day}`;

                    }

                }

            }
        );

    }
);