import sqlite3


def init_db():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()


    # =========================
    # TABEL ARTIKEL
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            keyword_id INTEGER,
            title TEXT NOT NULL,
            meta TEXT,
            article TEXT NOT NULL,
            score INTEGER DEFAULT 0,

            content_status TEXT DEFAULT 'Draft',
            published_url TEXT,
            index_status TEXT DEFAULT 'Belum Terindeks',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # =========================
    # TABEL KEYWORD TRACKER
    # =========================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            intent TEXT,
            source TEXT,
            status TEXT DEFAULT 'Riset',
            target_article TEXT,
            target_url TEXT,
            index_status TEXT DEFAULT 'Belum Terindeks',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # =========================
    # CEK KOLOM ARTICLES
    # =========================
    cursor.execute("PRAGMA table_info(articles)")

    columns = [
        column[1]
        for column in cursor.fetchall()
    ]


    # =========================
    # MIGRASI KEYWORD ID
    # =========================
    if "keyword_id" not in columns:

        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN keyword_id INTEGER
        """)

        print("Kolom keyword_id berhasil ditambahkan.")


    # =========================
    # MIGRASI STATUS ARTIKEL
    # =========================
    if "content_status" not in columns:

        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN content_status TEXT
            DEFAULT 'Draft'
        """)

        print("Kolom content_status berhasil ditambahkan.")


    # =========================
    # MIGRASI URL PUBLIK
    # =========================
    if "published_url" not in columns:

        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN published_url TEXT
        """)

        print("Kolom published_url berhasil ditambahkan.")


    # =========================
    # MIGRASI STATUS INDEX
    # =========================
    if "index_status" not in columns:

        cursor.execute("""
            ALTER TABLE articles
            ADD COLUMN index_status TEXT
            DEFAULT 'Belum Terindeks'
        """)

        print("Kolom index_status berhasil ditambahkan.")


    # =========================
    # HUBUNGKAN ARTIKEL LAMA
    # =========================
    cursor.execute("""
        UPDATE articles
        SET keyword_id = (
            SELECT keywords.id
            FROM keywords
            WHERE LOWER(TRIM(keywords.keyword))
                  = LOWER(TRIM(articles.keyword))
            LIMIT 1
        )
        WHERE keyword_id IS NULL
        AND EXISTS (
            SELECT 1
            FROM keywords
            WHERE LOWER(TRIM(keywords.keyword))
                  = LOWER(TRIM(articles.keyword))
        )
    """)


    # =========================
    # INDEX DATABASE
    # =========================
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_articles_keyword_id
        ON articles(keyword_id)
    """)


    conn.commit()
    conn.close()

    print("Database SFR SEO Tool berhasil diperbarui!")


if __name__ == "__main__":
    init_db()