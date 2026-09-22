import sqlite3
from flask import Flask, render_template, request, redirect
from search_console import (
    get_search_console_summary,
    get_top_queries,
    get_top_pages
)

app = Flask(__name__)


# =========================
# KONEKSI DATABASE
# =========================
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# =========================
# NORMALISASI TEKS
# =========================
def normalize_text(text):
    """
    Membuat pengecekan keyword lebih stabil:
    - huruf kecil
    - spasi ganda/baris baru dirapikan
    """
    return " ".join((text or "").casefold().split())


# =========================
# MESIN ANALISIS SEO
# =========================
def analisis_seo(keyword, title, meta, article):
    results = []
    score = 0

    keyword_normal = normalize_text(keyword)
    title_normal = normalize_text(title)
    meta_normal = normalize_text(meta)
    article_normal = normalize_text(article)

    word_count = len((article or "").split())

    # 1. KEYWORD DI JUDUL
    if keyword_normal and keyword_normal in title_normal:
        results.append({
            "status": "good",
            "text": "Keyword utama terdapat pada judul."
        })
        score += 20
    else:
        results.append({
            "status": "warning",
            "text": "Keyword utama belum terdapat pada judul."
        })

    # 2. PANJANG JUDUL
    title_length = len((title or "").strip())

    if 30 <= title_length <= 60:
        results.append({
            "status": "good",
            "text": f"Panjang judul {title_length} karakter."
        })
        score += 15
    else:
        results.append({
            "status": "warning",
            "text": (
                f"Panjang judul {title_length} karakter. "
                "Pertimbangkan sekitar 30–60 karakter."
            )
        })

    # 3. KEYWORD DI META DESCRIPTION
    if keyword_normal and keyword_normal in meta_normal:
        results.append({
            "status": "good",
            "text": "Keyword terdapat pada meta description."
        })
        score += 15
    else:
        results.append({
            "status": "warning",
            "text": "Keyword belum terdapat pada meta description."
        })

    # 4. PANJANG META DESCRIPTION
    meta_length = len((meta or "").strip())

    if 120 <= meta_length <= 160:
        results.append({
            "status": "good",
            "text": f"Meta description memiliki {meta_length} karakter."
        })
        score += 15
    else:
        results.append({
            "status": "warning",
            "text": (
                f"Meta description memiliki {meta_length} karakter. "
                "Pertimbangkan sekitar 120–160 karakter."
            )
        })

    # 5. PANJANG ARTIKEL
    if word_count >= 500:
        results.append({
            "status": "good",
            "text": f"Artikel memiliki {word_count} kata."
        })
        score += 15
    else:
        results.append({
            "status": "warning",
            "text": (
                f"Artikel baru memiliki {word_count} kata. "
                "Pertimbangkan memperdalam isi artikel."
            )
        })

    # 6. JUMLAH KEYWORD DI ARTIKEL
    keyword_count = (
        article_normal.count(keyword_normal)
        if keyword_normal
        else 0
    )

    if keyword_count > 0:
        results.append({
            "status": "good",
            "text": f"Keyword ditemukan {keyword_count} kali dalam artikel."
        })
        score += 10
    else:
        results.append({
            "status": "warning",
            "text": "Keyword utama belum ditemukan dalam isi artikel."
        })

    # 7. KEYWORD DI 100 KATA PERTAMA
    opening = normalize_text(" ".join((article or "").split()[:100]))

    if keyword_normal and keyword_normal in opening:
        results.append({
            "status": "good",
            "text": "Keyword muncul pada sekitar 100 kata pertama."
        })
        score += 10
    else:
        results.append({
            "status": "warning",
            "text": "Keyword belum muncul pada sekitar 100 kata pertama."
        })

    return results, score


# =========================
# DASHBOARD
# =========================
@app.route("/")
def home():

    conn = get_db_connection()
    cursor = conn.cursor()


    # =========================
    # TOTAL ARTIKEL
    # =========================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM articles
    """)

    total_articles = cursor.fetchone()["total"]


    # =========================
    # TOTAL KEYWORD
    # =========================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM keywords
    """)

    total_keywords = cursor.fetchone()["total"]


    # =========================
    # TOTAL PUBLISHED
    # =========================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM articles
        WHERE content_status = 'Published'
    """)

    total_published = cursor.fetchone()["total"]


    # =========================
    # TOTAL INDEXED
    # =========================
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM articles
        WHERE index_status = 'Indexed'
    """)

    total_indexed = cursor.fetchone()["total"]


    # =========================
    # ARTIKEL TERBARU
    # =========================
    cursor.execute("""
        SELECT
            id,
            title,
            keyword,
            score,
            content_status,
            index_status,
            created_at
        FROM articles
        ORDER BY id DESC
        LIMIT 5
    """)

    recent_articles = cursor.fetchall()


    # =========================
    # KEYWORD TERBARU
    # =========================
    cursor.execute("""
        SELECT
            id,
            keyword,
            intent,
            source,
            status,
            created_at
        FROM keywords
        ORDER BY id DESC
        LIMIT 5
    """)

    recent_keywords = cursor.fetchall()


    conn.close()


    return render_template(
        "dashboard.html",

        total_articles=total_articles,
        total_keywords=total_keywords,
        total_published=total_published,
        total_indexed=total_indexed,

        recent_articles=recent_articles,
        recent_keywords=recent_keywords
    )

# =========================
# ANALISIS SEO
# =========================
@app.route("/analisis", methods=["GET", "POST"])
def analisis():

    results = []
    score = 0

    keyword_id = ""
    keyword = ""
    title = ""
    meta = ""
    article = ""

    # =========================
    # AMBIL KEYWORD DARI TRACKER
    # =========================
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            keyword,
            intent,
            source,
            status
        FROM keywords
        ORDER BY id DESC
    """)

    keywords = cursor.fetchall()
    conn.close()

    # =========================
    # PROSES ANALISIS
    # =========================
    if request.method == "POST":

        keyword_id = request.form.get("keyword_id", "").strip()
        keyword = request.form.get("keyword", "").strip()
        title = request.form.get("title", "").strip()
        meta = request.form.get("meta", "").strip()
        article = request.form.get("article", "").strip()

        results, score = analisis_seo(
            keyword,
            title,
            meta,
            article
        )

    return render_template(
        "analisis.html",
        results=results,
        score=score,
        keyword_id=keyword_id,
        keyword=keyword,
        title=title,
        meta=meta,
        article=article,
        keywords=keywords
    )


# =========================
# SIMPAN ARTIKEL
# =========================
@app.route("/simpan", methods=["POST"])
def simpan_artikel():

    keyword_id_raw = request.form.get(
        "keyword_id",
        ""
    ).strip()

    keyword = request.form.get(
        "keyword",
        ""
    ).strip()

    title = request.form.get(
        "title",
        ""
    ).strip()

    meta = request.form.get(
        "meta",
        ""
    ).strip()

    article = request.form.get(
        "article",
        ""
    ).strip()


    # =========================
    # KEYWORD ID
    # =========================
    if keyword_id_raw.isdigit():
        keyword_id = int(keyword_id_raw)
    else:
        keyword_id = None


    # =========================
    # HITUNG ON-PAGE SEO SCORE
    # =========================
    _, score = analisis_seo(
        keyword,
        title,
        meta,
        article
    )


    conn = get_db_connection()
    cursor = conn.cursor()


    # =========================
    # SIMPAN ARTIKEL
    # =========================
    cursor.execute("""
        INSERT INTO articles (
            keyword,
            keyword_id,
            title,
            meta,
            article,
            score,
            content_status,
            index_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        keyword,
        keyword_id,
        title,
        meta,
        article,
        score,
        "Draft",
        "Belum Terindeks"
    ))


    # =========================
    # UPDATE KEYWORD TRACKER
    # =========================
    if keyword_id is not None:

        cursor.execute("""
            UPDATE keywords
            SET
                target_article = ?,
                status = CASE
                    WHEN status = 'Riset'
                    THEN 'Draft'
                    ELSE status
                END
            WHERE id = ?
        """, (
            title,
            keyword_id
        ))


    conn.commit()
    conn.close()


    return redirect("/artikel")

# =========================
# ARTIKEL SAYA
# =========================
@app.route("/artikel")
def artikel_saya():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            keyword,
            keyword_id,
            title,
            meta,
            article,
            score,
            content_status,
            published_url,
            index_status,
            created_at
        FROM articles
        ORDER BY id DESC
    """)

    articles = cursor.fetchall()

    conn.close()

    return render_template(
        "artikel.html",
        articles=articles
    )

# =========================
# DETAIL ARTIKEL
# =========================
@app.route("/artikel/<int:article_id>")
def detail_artikel(article_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM articles
        WHERE id = ?
    """, (article_id,))

    article = cursor.fetchone()
    conn.close()

    if article is None:
        return "Artikel tidak ditemukan", 404

    return render_template(
        "detail_artikel.html",
        article=article
    )


# =========================
# EDIT ARTIKEL
# =========================
@app.route("/artikel/<int:article_id>/edit", methods=["GET", "POST"])
def edit_artikel(article_id):

    conn = get_db_connection()
    cursor = conn.cursor()


    # =========================
    # AMBIL DATA ARTIKEL
    # =========================
    cursor.execute("""
        SELECT *
        FROM articles
        WHERE id = ?
    """, (article_id,))

    article = cursor.fetchone()


    if article is None:
        conn.close()
        return "Artikel tidak ditemukan", 404


    # =========================
    # SIMPAN PERUBAHAN
    # =========================
    if request.method == "POST":

        keyword = request.form.get(
            "keyword",
            ""
        ).strip()

        title = request.form.get(
            "title",
            ""
        ).strip()

        meta = request.form.get(
            "meta",
            ""
        ).strip()

        article_text = request.form.get(
            "article",
            ""
        ).strip()

        content_status = request.form.get(
            "content_status",
            "Draft"
        ).strip()

        published_url = request.form.get(
            "published_url",
            ""
        ).strip()

        index_status = request.form.get(
            "index_status",
            "Belum Terindeks"
        ).strip()


        # =========================
        # HITUNG ULANG SEO SCORE
        # =========================
        _, score_baru = analisis_seo(
            keyword,
            title,
            meta,
            article_text
        )


        # =========================
        # UPDATE ARTIKEL
        # =========================
        cursor.execute("""
            UPDATE articles
            SET
                keyword = ?,
                title = ?,
                meta = ?,
                article = ?,
                score = ?,
                content_status = ?,
                published_url = ?,
                index_status = ?
            WHERE id = ?
        """, (
            keyword,
            title,
            meta,
            article_text,
            score_baru,
            content_status,
            published_url,
            index_status,
            article_id
        ))


        # =========================
        # SINKRONKAN KEYWORD TRACKER
        # =========================
        if article["keyword_id"] is not None:

            cursor.execute("""
                UPDATE keywords
                SET
                    target_article = ?,
                    target_url = ?,
                    status = ?,
                    index_status = ?
                WHERE id = ?
            """, (
                title,
                published_url,
                content_status,
                index_status,
                article["keyword_id"]
            ))


        conn.commit()
        conn.close()

        return redirect(
            f"/artikel/{article_id}"
        )


    conn.close()


    return render_template(
        "edit_artikel.html",
        article=article
    )
# =========================
# ANALISIS ULANG SEO
# =========================
@app.route("/artikel/<int:article_id>/analisis-ulang", methods=["POST"])
def analisis_ulang_artikel(article_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM articles
        WHERE id = ?
    """, (article_id,))

    article = cursor.fetchone()

    if article is None:
        conn.close()
        return "Artikel tidak ditemukan", 404

    _, score_baru = analisis_seo(
        article["keyword"],
        article["title"],
        article["meta"],
        article["article"]
    )

    cursor.execute("""
        UPDATE articles
        SET score = ?
        WHERE id = ?
    """, (
        score_baru,
        article_id
    ))

    conn.commit()
    conn.close()

    return redirect(f"/artikel/{article_id}")


# =========================
# HAPUS ARTIKEL
# =========================
@app.route("/artikel/<int:article_id>/hapus", methods=["POST"])
def hapus_artikel(article_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM articles
        WHERE id = ?
    """, (article_id,))

    conn.commit()
    conn.close()

    return redirect("/artikel")


# =========================
# JALANKAN APLIKASI
# =========================

# =========================
# KEYWORD TRACKER
# =========================
@app.route("/keyword", methods=["GET", "POST"])
def keyword_tracker():

    conn = get_db_connection()
    cursor = conn.cursor()

    # =========================
    # SIMPAN KEYWORD
    # =========================
    if request.method == "POST":

        keyword = request.form.get("keyword", "").strip()
        intent = request.form.get("intent", "").strip()
        source = request.form.get("source", "").strip()
        status = request.form.get("status", "Riset").strip()
        target_article = request.form.get("target_article", "").strip()
        target_url = request.form.get("target_url", "").strip()
        index_status = request.form.get(
            "index_status",
            "Belum Terindeks"
        ).strip()
        notes = request.form.get("notes", "").strip()

        cursor.execute("""
            INSERT INTO keywords (
                keyword,
                intent,
                source,
                status,
                target_article,
                target_url,
                index_status,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            keyword,
            intent,
            source,
            status,
            target_article,
            target_url,
            index_status,
            notes
        ))

        conn.commit()
        conn.close()

        return redirect("/keyword")


    # =========================
    # AMBIL SEMUA KEYWORD
    # =========================
    cursor.execute("""
        SELECT
            id,
            keyword,
            intent,
            source,
            status,
            target_article,
            target_url,
            index_status,
            notes,
            created_at
        FROM keywords
        ORDER BY id DESC
    """)

    keywords = cursor.fetchall()

    conn.close()


    return render_template(
        "keyword.html",
        keywords=keywords
    )

# =========================
# DETAIL KEYWORD
# =========================
@app.route("/keyword/<int:keyword_id>")
def detail_keyword(keyword_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # AMBIL DATA KEYWORD
    cursor.execute("""
        SELECT *
        FROM keywords
        WHERE id = ?
    """, (keyword_id,))

    keyword = cursor.fetchone()

    if keyword is None:
        conn.close()
        return "Keyword tidak ditemukan", 404

    # AMBIL ARTIKEL TERHUBUNG
    cursor.execute("""
        SELECT
            id,
            title,
            keyword,
            score,
            created_at
        FROM articles
        WHERE keyword_id = ?
        ORDER BY id DESC
    """, (keyword_id,))

    linked_articles = cursor.fetchall()

    conn.close()

    return render_template(
        "detail_keyword.html",
        keyword=keyword,
        linked_articles=linked_articles
    )


# =========================
# EDIT KEYWORD
# =========================
@app.route("/keyword/<int:keyword_id>/edit", methods=["GET", "POST"])
def edit_keyword(keyword_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # AMBIL DATA KEYWORD
    cursor.execute("""
        SELECT *
        FROM keywords
        WHERE id = ?
    """, (keyword_id,))

    keyword = cursor.fetchone()

    if keyword is None:
        conn.close()
        return "Keyword tidak ditemukan", 404

    # SIMPAN PERUBAHAN
    if request.method == "POST":

        new_keyword = request.form.get(
            "keyword",
            ""
        ).strip()

        intent = request.form.get(
            "intent",
            ""
        ).strip()

        source = request.form.get(
            "source",
            ""
        ).strip()

        status = request.form.get(
            "status",
            ""
        ).strip()

        target_article = request.form.get(
            "target_article",
            ""
        ).strip()

        target_url = request.form.get(
            "target_url",
            ""
        ).strip()

        index_status = request.form.get(
            "index_status",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        cursor.execute("""
            UPDATE keywords
            SET
                keyword = ?,
                intent = ?,
                source = ?,
                status = ?,
                target_article = ?,
                target_url = ?,
                index_status = ?,
                notes = ?
            WHERE id = ?
        """, (
            new_keyword,
            intent,
            source,
            status,
            target_article,
            target_url,
            index_status,
            notes,
            keyword_id
        ))

        conn.commit()
        conn.close()

        return redirect(
            f"/keyword/{keyword_id}"
        )

    conn.close()

    return render_template(
        "edit_keyword.html",
        keyword=keyword
    )

# =========================
# HAPUS KEYWORD
# =========================
@app.route("/keyword/<int:keyword_id>/hapus", methods=["POST"])
def hapus_keyword(keyword_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    # Lepaskan hubungan artikel dengan keyword
    # Artikelnya tetap ada
    cursor.execute("""
        UPDATE articles
        SET keyword_id = NULL
        WHERE keyword_id = ?
    """, (keyword_id,))

    # Hapus keyword
    cursor.execute("""
        DELETE FROM keywords
        WHERE id = ?
    """, (keyword_id,))

    conn.commit()
    conn.close()

    return redirect("/keyword")

# =========================
# GOOGLE SEARCH CONSOLE
# =========================
@app.route("/search-console")
def search_console():

    try:
        data = get_search_console_summary()
        queries = get_top_queries()
        pages = get_top_pages()

        error = None

    except Exception as e:

        data = {
            "site_url": "https://sfrcreativeid.blogspot.com/",
            "start_date": "-",
            "end_date": "-",
            "clicks": 0,
            "impressions": 0,
            "ctr": 0,
            "position": 0
        }

        queries = []
        pages = []

        error = "Data Google Search Console sedang tidak dapat diambil."

        print("Search Console Error:", e)

    return render_template(
        "search_console.html",
        data=data,
        queries=queries,
        pages=pages,
        error=error
    )

if __name__ == "__main__":
    app.run(debug=True)
