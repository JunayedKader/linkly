import os
import random
import string
import psycopg2
import redis
import validators
from flask import Flask, jsonify, redirect, render_template, request
app = Flask(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "linkly")
DB_USER = os.environ.get("DB_USER", "linkly")
DB_PASS = os.environ.get("DB_PASS", "linkly")

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


def generate_short_code(length=6):
    # Build a pool of characters to pick from.
    # string.ascii_letters = abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
    # string.digits = 0123456789
    # Combined pool has 62 characters — 62^6 = ~56 billion combinations,
    # more than enough to avoid collisions for a learning project.
    characters = string.ascii_letters + string.digits

    # random.choices picks `length` characters from the pool independently,
    # allowing repeats (e.g. "aaBc3k" is valid).
    # ''.join() combines the list of characters into a single string.
    return ''.join(random.choices(characters, k=length))


@app.route("/")
def health():
    return jsonify({"status": "ok", "env": APP_ENV})

@app.route("/ui")
def ui():
    # render_template looks for files in the templates/ directory
    # relative to the app.py file location.
    # Flask finds app/templates/index.html automatically.
    return render_template("index.html")

@app.route("/db")
def db_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({"db": "connected"})
    except Exception as e:
        return jsonify({"db": "error", "detail": str(e)}), 500


@app.route("/cache")
def cache_check():
    try:
        count = redis_client.get("hit_count")
        if count is None:
            redis_client.set("hit_count", 1)
            count = 1
        else:
            count = redis_client.incr("hit_count")
        return jsonify({"cache": "connected", "hit_count": int(count)})
    except Exception as e:
        return jsonify({"cache": "error", "detail": str(e)}), 500


@app.route("/shorten", methods=["POST"])
def shorten():
    # request.get_json() parses the request body as JSON.
    # silent=True returns None instead of raising an error if body
    # is not valid JSON — we handle the None case below.
    data = request.get_json(silent=True)

    # Validate that request body exists and contains "url" key.
    if not data or "url" not in data:
        return jsonify({
            "error": "Request body must be JSON with a 'url' field",
            "example": {"url": "https://example.com"}
        }), 400
        # 400 Bad Request — client sent an invalid request

    original_url = data["url"]

    # validators.url() returns True if the string is a valid URL,
    # a ValidationError object (truthy) if it's not.
    # We explicitly check for True to be safe.
    if not validators.url(original_url):
        return jsonify({
            "error": "Invalid URL — must include scheme (http:// or https://)",
            "received": original_url
        }), 422
        # 422 Unprocessable Entity — request was understood but
        # the value failed validation

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Collision-resistant short code generation.
        # In the unlikely event a generated code already exists in the DB,
        # we generate a new one and try again — up to 5 attempts.
        # After 5 failures we give up and return a 500 error.
        # At 62^6 combinations this loop almost never runs more than once.
        max_attempts = 5
        short_code = None

        for attempt in range(max_attempts):
            candidate = generate_short_code()

            # Check if this code is already taken.
            cur.execute(
                "SELECT id FROM links WHERE short_code = %s",
                (candidate,)
            )
            # fetchone() returns a row tuple if found, None if not.
            if cur.fetchone() is None:
                # Code is available — use it.
                short_code = candidate
                break

        if short_code is None:
            return jsonify({"error": "Failed to generate unique code"}), 500

        # Insert the new link into the database.
        # RETURNING created_at retrieves the auto-generated timestamp
        # without needing a second SELECT query.
        cur.execute(
            """
            INSERT INTO links (short_code, original_url)
            VALUES (%s, %s)
            RETURNING created_at
            """,
            (short_code, original_url)
        )
        created_at = cur.fetchone()[0]

        # conn.commit() writes the transaction to disk.
        # Without this, the INSERT is rolled back when the connection closes.
        conn.commit()
        cur.close()
        conn.close()

        # Cache the mapping in Redis for fast redirect lookups.
        # Key: "link:<short_code>", Value: original_url
        # expire=3600 sets a 1-hour TTL — after that Redis evicts the key
        # and the next redirect falls back to PostgreSQL.
        redis_client.set(
            f"link:{short_code}",
            original_url,
            ex=3600
        )

        # Build the full short URL using the Host header from the request.
        # request.host returns "localhost" or the actual domain in production.
        short_url = f"http://{request.host}/{short_code}"

        return jsonify({
            "short_url": short_url,
            "short_code": short_code,
            "original_url": original_url,
            "created_at": created_at.isoformat()
        }), 201
        # 201 Created — resource was successfully created

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/<short_code>")
def redirect_to_url(short_code):
    # Step 1 — check Redis cache first (fast path).
    # If the mapping is cached, we never touch PostgreSQL.
    # This is the core purpose of Redis in a URL shortener —
    # redirects are read-heavy, caching eliminates DB load.
    try:
        cached_url = redis_client.get(f"link:{short_code}")
        if cached_url:
            # Increment click count in PostgreSQL asynchronously
            # would be ideal, but for simplicity we do it inline.
            _increment_click_count(short_code)
            # 302 Found — temporary redirect.
            # Browser follows the Location header to the original URL.
            return redirect(cached_url, code=302)
    except Exception:
        # Redis is down or unavailable — fall through to PostgreSQL.
        # We never let a cache failure break the redirect.
        pass

    # Step 2 — cache miss, query PostgreSQL (slow path).
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT original_url FROM links WHERE short_code = %s",
            (short_code,)
        )
        row = cur.fetchone()

        if row is None:
            cur.close()
            conn.close()
            return jsonify({"error": f"Short code '{short_code}' not found"}), 404

        original_url = row[0]

        # Re-populate Redis cache for next request.
        # ex=3600 — 1 hour TTL, same as on creation.
        try:
            redis_client.set(f"link:{short_code}", original_url, ex=3600)
        except Exception:
            pass  # Cache failure is non-fatal

        _increment_click_count(short_code)

        cur.close()
        conn.close()

        return redirect(original_url, code=302)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _increment_click_count(short_code):
    # Increment click_count in PostgreSQL for analytics.
    # This is a separate function because both the cache hit
    # and cache miss paths need to call it.
    # Errors here are silently ignored — a failed counter increment
    # should never break a redirect.
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE links SET click_count = click_count + 1 WHERE short_code = %s",
            (short_code,)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


@app.route("/links", methods=["GET"])
def list_links():
    # Returns all shortened URLs — useful for verifying the app works.
    # In a real product this would be paginated and auth-protected.
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT short_code, original_url, created_at, click_count
            FROM links
            ORDER BY created_at DESC
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        links = [
            {
                "short_code": row[0],
                "original_url": row[1],
                "created_at": row[2].isoformat(),
                "click_count": row[3],
                "short_url": f"http://{request.host}/{row[0]}"
            }
            for row in rows
        ]

        return jsonify({"count": len(links), "links": links})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
