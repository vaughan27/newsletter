from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
    send_from_directory,
    make_response,
    session,
)

import sqlite3
import os
import re
import uuid
import io

from dotenv import load_dotenv
load_dotenv()

import pymupdf
from PIL import Image


# ==================================================
# CONFIGURATION
# ==================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE = os.path.join(
    BASE_DIR,
    "database.db"
)

PDF_FOLDER = os.path.join(
    BASE_DIR,
    "pdfs"
)

COVER_FOLDER = os.path.join(
    BASE_DIR,
    "covers"
)

ALLOWED_EXTENSIONS = {
    "pdf"
}

MAX_FILE_SIZE = 50 * 1024 * 1024

VISITOR_COOKIE = "newsletter_visitor_id"


# ==================================================
# FLASK
# ==================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "UT&^%NI#@!G#%$^&*()_+"
)

app.config["MAX_CONTENT_LENGTH"] = (
    MAX_FILE_SIZE
)


# ==================================================
# ADMIN TOKEN
# ==================================================

ADMIN_TOKEN = os.environ.get(
    "NEWSLETTER_ADMIN_TOKEN",
    "AdminToken###"
)


# ==================================================
# CREATE DIRECTORIES
# ==================================================

os.makedirs(
    PDF_FOLDER,
    exist_ok=True
)

os.makedirs(
    COVER_FOLDER,
    exist_ok=True
)


# ==================================================
# DATABASE
# ==================================================

def get_db():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


def init_db():

    connection = get_db()

    # ----------------------------------------------
    # NEWSLETTERS
    # ----------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS newsletters (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            publication_date TEXT NOT NULL,

            description TEXT,

            pdf_filename TEXT NOT NULL,

            cover_filename TEXT,

            extracted_text TEXT,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    # ----------------------------------------------
    # DOWNLOADS
    # ----------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS newsletter_downloads (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            newsletter_id INTEGER NOT NULL,

            downloaded_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (newsletter_id)
                REFERENCES newsletters(id)

        )
        """
    )

    # ----------------------------------------------
    # SITE VISITS
    # ----------------------------------------------

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS site_visits (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            visitor_id TEXT NOT NULL,

            visited_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
        """
    )

    connection.commit()

    connection.close()


# ==================================================
# HELPERS
# ==================================================

def allowed_file(filename):

    return (
        "."
        in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


def clean_filename(filename):

    filename = os.path.basename(
        filename
    )

    filename = re.sub(
        r"[^a-zA-Z0-9._-]",
        "_",
        filename
    )

    return filename


def extract_pdf_text(pdf_path):

    document = pymupdf.open(
        pdf_path
    )

    text = []

    for page in document:

        page_text = page.get_text()

        if page_text:
            text.append(
                page_text
            )

    document.close()

    return "\n\n".join(
        text
    )


def generate_cover(
    pdf_path,
    cover_path
):

    document = pymupdf.open(
        pdf_path
    )

    if len(document) == 0:

        document.close()

        return False

    page = document[0]

    # ----------------------------------------------
    # RENDER FIRST PAGE
    # ----------------------------------------------

    pixmap = page.get_pixmap(
        matrix=pymupdf.Matrix(
            1.5,
            1.5
        ),
        alpha=False
    )

    # ----------------------------------------------
    # CONVERT TO PIL
    # ----------------------------------------------

    image = Image.open(
        io.BytesIO(
            pixmap.tobytes("png")
        )
    )

    width, height = image.size

    # ----------------------------------------------
    # CROP TO 16:9
    # ----------------------------------------------

    target_ratio = 16 / 9

    current_ratio = (
        width / height
    )

    if current_ratio > target_ratio:

        # Image too wide.
        # Crop left and right.

        new_width = int(
            height * target_ratio
        )

        left = int(
            (width - new_width) / 2
        )

        right = (
            left
            + new_width
        )

        image = image.crop(
            (
                left,
                0,
                right,
                height
            )
        )

    elif current_ratio < target_ratio:

        # Image too tall.
        # Crop top and bottom.

        new_height = int(
            width / target_ratio
        )

        top = int(
            (height - new_height) / 2
        )

        bottom = (
            top
            + new_height
        )

        image = image.crop(
            (
                0,
                top,
                width,
                bottom
            )
        )

    # ----------------------------------------------
    # SAVE
    # ----------------------------------------------

    image.save(
        cover_path,
        "PNG"
    )

    document.close()

    return True


# ==================================================
# HOME
# ==================================================

@app.route("/")
def index():

    # ----------------------------------------------
    # IDENTIFY VISITOR
    # ----------------------------------------------

    visitor_id = request.cookies.get(
        VISITOR_COOKIE
    )

    new_visitor = False

    if not visitor_id:

        visitor_id = uuid.uuid4().hex

        new_visitor = True

    # ----------------------------------------------
    # DATABASE
    # ----------------------------------------------

    connection = get_db()

    connection.execute(
        """
        INSERT INTO site_visits (
            visitor_id
        )
        VALUES (?)
        """,
        (visitor_id,)
    )

    connection.commit()

    # ----------------------------------------------
    # NEWSLETTERS
    # ----------------------------------------------

    newsletters = connection.execute(
        """
        SELECT *
        FROM newsletters
        ORDER BY publication_date DESC
        """
    ).fetchall()

    # ----------------------------------------------
    # YEARS
    # ----------------------------------------------

    years = connection.execute(
        """
        SELECT
            substr(
                publication_date,
                1,
                4
            ) AS year,

            COUNT(*) AS count

        FROM newsletters

        GROUP BY year

        ORDER BY year DESC
        """
    ).fetchall()

    connection.close()

    # ----------------------------------------------
    # LATEST YEAR
    # ----------------------------------------------

    latest_year = None

    if years:

        latest_year = years[0]["year"]

    # ----------------------------------------------
    # RESPONSE
    # ----------------------------------------------

    response = make_response(
        render_template(
            "index.html",
            newsletters=newsletters,
            years=years,
            latest_year=latest_year
        )
    )

    # ----------------------------------------------
    # SAVE VISITOR COOKIE
    # ----------------------------------------------

    if new_visitor:

        response.set_cookie(
            VISITOR_COOKIE,
            visitor_id,
            max_age=60 * 60 * 24 * 365 * 2,
            httponly=True,
            samesite="Lax"
        )

    return response


# ==================================================
# NEWSLETTER PAGE
# ==================================================

@app.route(
    "/newsletter/<int:newsletter_id>"
)
def newsletter(newsletter_id):

    connection = get_db()

    newsletter = connection.execute(
        """
        SELECT *
        FROM newsletters
        WHERE id = ?
        """,
        (newsletter_id,)
    ).fetchone()

    connection.close()

    if newsletter is None:

        return (
            "Newsletter not found",
            404
        )

    return render_template(
        "newsletter.html",
        newsletter=newsletter
    )


# ==================================================
# PDF FILES / DOWNLOAD TRACKING
# ==================================================

@app.route(
    "/pdfs/<filename>"
)
def pdf_file(filename):

    connection = get_db()

    newsletter = connection.execute(
        """
        SELECT id
        FROM newsletters
        WHERE pdf_filename = ?
        """,
        (filename,)
    ).fetchone()

    if newsletter is None:

        connection.close()

        return (
            "PDF not found",
            404
        )

    # ----------------------------------------------
    # RECORD DOWNLOAD
    # ----------------------------------------------

    connection.execute(
        """
        INSERT INTO newsletter_downloads (
            newsletter_id
        )
        VALUES (?)
        """,
        (newsletter["id"],)
    )

    connection.commit()

    connection.close()

    # ----------------------------------------------
    # SEND PDF
    # ----------------------------------------------

    return send_from_directory(
        PDF_FOLDER,
        filename
    )


# ==================================================
# COVER FILES
# ==================================================

@app.route(
    "/covers/<filename>"
)
def cover_file(filename):

    return send_from_directory(
        COVER_FOLDER,
        filename
    )


# ==================================================
# SEARCH API
# ==================================================

@app.route(
    "/api/search"
)
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    if not query:

        return jsonify([])

    connection = get_db()

    search_pattern = (
        "%"
        + query
        + "%"
    )

    results = connection.execute(
        """
        SELECT
            id,
            title,
            publication_date,
            description,
            cover_filename

        FROM newsletters

        WHERE
            title LIKE ?
            OR description LIKE ?
            OR extracted_text LIKE ?

        ORDER BY publication_date DESC

        LIMIT 100
        """,
        (
            search_pattern,
            search_pattern,
            search_pattern
        )
    ).fetchall()

    connection.close()

    return jsonify([

        {
            "id": row["id"],

            "title": row["title"],

            "date":
                row["publication_date"],

            "description":
                row["description"],

            "cover":
                (
                    url_for(
                        "cover_file",
                        filename=row[
                            "cover_filename"
                        ]
                    )
                    if row["cover_filename"]
                    else None
                ),

            "url":
                url_for(
                    "newsletter",
                    newsletter_id=row["id"]
                )
        }

        for row in results

    ])


# ==================================================
# UPLOAD PAGE
# ==================================================

@app.route(
    "/admin/upload",
    methods=["GET"]
)
def upload_page():

    return render_template(
        "upload.html"
    )


# ==================================================
# UPLOAD NEWSLETTER
# ==================================================

@app.route(
    "/admin/upload",
    methods=["POST"]
)
def upload():

    pdf = request.files.get(
        "pdf"
    )

    title = request.form.get(
        "title",
        ""
    ).strip()

    publication_date = request.form.get(
        "publication_date",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    # ----------------------------------------------
    # VALIDATION
    # ----------------------------------------------

    if not pdf:

        flash(
            "Please select a PDF.",
            "error"
        )

        return redirect(
            url_for(
                "upload_page"
            )
        )

    if not allowed_file(
        pdf.filename
    ):

        flash(
            "Only PDF files are allowed.",
            "error"
        )

        return redirect(
            url_for(
                "upload_page"
            )
        )

    if not title:

        flash(
            "Please enter a title.",
            "error"
        )

        return redirect(
            url_for(
                "upload_page"
            )
        )

    if not publication_date:

        flash(
            "Please enter a publication date.",
            "error"
        )

        return redirect(
            url_for(
                "upload_page"
            )
        )

    # ----------------------------------------------
    # FILE NAMES
    # ----------------------------------------------

    original_name = clean_filename(
        pdf.filename
    )

    unique_id = uuid.uuid4().hex[:8]

    pdf_filename = (
        f"{publication_date}"
        f"_{unique_id}_"
        f"{original_name}"
    )

    pdf_path = os.path.join(
        PDF_FOLDER,
        pdf_filename
    )

    cover_filename = (
        os.path.splitext(
            pdf_filename
        )[0]
        + ".png"
    )

    cover_path = os.path.join(
        COVER_FOLDER,
        cover_filename
    )

    # ----------------------------------------------
    # SAVE PDF
    # ----------------------------------------------

    pdf.save(
        pdf_path
    )

    try:

        # ------------------------------------------
        # EXTRACT TEXT
        # ------------------------------------------

        extracted_text = (
            extract_pdf_text(
                pdf_path
            )
        )

        # ------------------------------------------
        # GENERATE COVER
        # ------------------------------------------

        if not generate_cover(
            pdf_path,
            cover_path
        ):

            raise Exception(
                "Could not generate newsletter cover."
            )

        # ------------------------------------------
        # DATABASE
        # ------------------------------------------

        connection = get_db()

        connection.execute(
            """
            INSERT INTO newsletters (

                title,
                publication_date,
                description,
                pdf_filename,
                cover_filename,
                extracted_text

            )

            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                publication_date,
                description,
                pdf_filename,
                cover_filename,
                extracted_text
            )
        )

        connection.commit()

        connection.close()

    except Exception as error:

        print(
            "UPLOAD ERROR:",
            error
        )

        # ------------------------------------------
        # CLEAN UP PDF
        # ------------------------------------------

        if os.path.exists(
            pdf_path
        ):

            os.remove(
                pdf_path
            )

        # ------------------------------------------
        # CLEAN UP COVER
        # ------------------------------------------

        if os.path.exists(
            cover_path
        ):

            os.remove(
                cover_path
            )

        flash(
            "There was a problem processing the PDF.",
            "error"
        )

        return redirect(
            url_for(
                "upload_page"
            )
        )

    flash(
        "Newsletter uploaded successfully.",
        "success"
    )

    return redirect(
        url_for(
            "index"
        )
    )


# ==================================================
# DELETE NEWSLETTER
# ==================================================

@app.route(
    "/admin/delete/<int:newsletter_id>",
    methods=["POST"]
)
def delete_newsletter(newsletter_id):

    token = request.headers.get(
        "X-Admin-Token"
    )

    if not token or token != ADMIN_TOKEN:

        return jsonify({
            "error": "Unauthorized"
        }), 401

    connection = get_db()

    newsletter = connection.execute(
        """
        SELECT *
        FROM newsletters
        WHERE id = ?
        """,
        (newsletter_id,)
    ).fetchone()

    if newsletter is None:

        connection.close()

        return jsonify({
            "error": "Newsletter not found"
        }), 404

    # ----------------------------------------------
    # PDF PATH
    # ----------------------------------------------

    pdf_path = os.path.join(
        PDF_FOLDER,
        newsletter["pdf_filename"]
    )

    # ----------------------------------------------
    # COVER PATH
    # ----------------------------------------------

    cover_path = None

    if newsletter["cover_filename"]:

        cover_path = os.path.join(
            COVER_FOLDER,
            newsletter["cover_filename"]
        )

    # ----------------------------------------------
    # DELETE PDF
    # ----------------------------------------------

    if os.path.exists(
        pdf_path
    ):

        os.remove(
            pdf_path
        )

    # ----------------------------------------------
    # DELETE COVER
    # ----------------------------------------------

    if (
        cover_path
        and
        os.path.exists(
            cover_path
        )
    ):

        os.remove(
            cover_path
        )

    # ----------------------------------------------
    # DELETE DOWNLOAD STATISTICS
    # ----------------------------------------------

    connection.execute(
        """
        DELETE FROM newsletter_downloads
        WHERE newsletter_id = ?
        """,
        (newsletter_id,)
    )

    # ----------------------------------------------
    # DELETE NEWSLETTER
    # ----------------------------------------------

    connection.execute(
        """
        DELETE FROM newsletters
        WHERE id = ?
        """,
        (newsletter_id,)
    )

    connection.commit()

    connection.close()

    return jsonify({
        "success": True,
        "message": "Newsletter deleted"
    })

# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if not session.get(
        "dashboard_authenticated"
    ):
        return redirect(
            url_for("dashboard_login")
        )

    connection = get_db()

    # --------------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------------

    total_newsletters = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM newsletters
        """
    ).fetchone()["count"]

    total_visits = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM site_visits
        """
    ).fetchone()["count"]

    unique_visitors = connection.execute(
        """
        SELECT COUNT(DISTINCT visitor_id) AS count
        FROM site_visits
        """
    ).fetchone()["count"]

    total_downloads = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM newsletter_downloads
        """
    ).fetchone()["count"]

    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    today_visits = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM site_visits
        WHERE DATE(visited_at) = DATE('now', 'localtime')
        """
    ).fetchone()["count"]

    today_unique_visitors = connection.execute(
        """
        SELECT COUNT(DISTINCT visitor_id) AS count
        FROM site_visits
        WHERE DATE(visited_at) = DATE('now', 'localtime')
        """
    ).fetchone()["count"]

    today_downloads = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM newsletter_downloads
        WHERE DATE(downloaded_at) = DATE('now', 'localtime')
        """
    ).fetchone()["count"]

    # --------------------------------------------------------
    # DOWNLOADS BY NEWSLETTER
    # --------------------------------------------------------

    downloads_by_newsletter = connection.execute(
        """
        SELECT
            n.title,
            n.publication_date,
            COUNT(d.id) AS downloads
        FROM newsletters n
        LEFT JOIN newsletter_downloads d
            ON d.newsletter_id = n.id
        GROUP BY n.id
        ORDER BY downloads DESC, n.publication_date DESC
        """
    ).fetchall()

    # --------------------------------------------------------
    # DAILY TRAFFIC
    # --------------------------------------------------------

    daily_visits = connection.execute(
        """
        SELECT
            DATE(visited_at) AS visit_date,
            COUNT(*) AS visits,
            COUNT(DISTINCT visitor_id) AS unique_visitors
        FROM site_visits
        GROUP BY DATE(visited_at)
        ORDER BY visit_date DESC
        LIMIT 30
        """
    ).fetchall()

    # --------------------------------------------------------
    # DAILY DOWNLOADS
    # --------------------------------------------------------

    daily_downloads = connection.execute(
        """
        SELECT
            DATE(downloaded_at) AS download_date,
            COUNT(*) AS downloads
        FROM newsletter_downloads
        GROUP BY DATE(downloaded_at)
        ORDER BY download_date DESC
        LIMIT 30
        """
    ).fetchall()

    # --------------------------------------------------------
    # RECENT DOWNLOADS
    # --------------------------------------------------------

    recent_downloads = connection.execute(
        """
        SELECT
            n.title,
            d.downloaded_at
        FROM newsletter_downloads d
        JOIN newsletters n
            ON n.id = d.newsletter_id
        ORDER BY d.downloaded_at DESC
        LIMIT 20
        """
    ).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        total_newsletters=total_newsletters,
        total_visits=total_visits,
        unique_visitors=unique_visitors,
        total_downloads=total_downloads,
        today_visits=today_visits,
        today_unique_visitors=today_unique_visitors,
        today_downloads=today_downloads,
        downloads_by_newsletter=downloads_by_newsletter,
        daily_visits=daily_visits,
        daily_downloads=daily_downloads,
        recent_downloads=recent_downloads
    )


# ==================================================
# START
# ==================================================

if __name__ == "__main__":

    # ============================================================
    # DASHBOARD AUTHENTICATION
    # ============================================================

    @app.route("/dashboard/login", methods=["GET", "POST"])
    def dashboard_login():

        if request.method == "POST":

            token = request.form.get("token", "")

            if token == ADMIN_TOKEN:

                session["dashboard_authenticated"] = True

                return redirect(
                    url_for("dashboard")
                )

            return render_template(
                "dashboard_login.html",
                error="Invalid admin token."
            )

        return render_template(
            "dashboard_login.html"
        )


    @app.route("/dashboard/logout")
    def dashboard_logout():

        session.pop(
            "dashboard_authenticated",
            None
        )

        return redirect(
            url_for("dashboard_login")
        )

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )