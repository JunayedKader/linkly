import os
import redis
import psycopg2
from flask import Flask

app = Flask(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")

# Read individual DB connection pieces from environment variables.
# These are injected by Compose via the `environment:` block — the app
# itself never hardcodes credentials.
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "linkly")
DB_USER = os.environ.get("DB_USER", "linkly")
DB_PASS = os.environ.get("DB_PASS", "linkly")


# Redis connection details injected from environment — same pattern as DB.
# decode_responses=True tells the client to return Python strings instead
# of raw bytes. Without it, get("key") returns b"value" instead of "value".
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)


def get_db_connection():
    # Opens a fresh connection each time it's called.
    # No connection pooling yet — that comes later when we add Redis.
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )



@app.route("/")
def health():
    return {"status": "ok", "env": APP_ENV}


@app.route("/db")
def db_check():
    # Tries to open a connection and run the simplest possible query.
    # SELECT 1 returns a single row with value 1 — it proves the connection
    # works without touching any real table.
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"db": "connected"}
    except Exception as e:
        # Returns the error as a string so you can see exactly what failed
        # in the browser or curl output — useful for debugging connection issues.
        return {"db": "error", "detail": str(e)}, 500



@app.route("/cache")
def cache_check():
    # Tries to read a key called "hit_count" from Redis.
    # If it doesn't exist yet, get() returns None.
    try:
        count = redis_client.get("hit_count")

        if count is None:
            # Key doesn't exist — first visit. Set it to 1.
            # This also demonstrates that Redis starts empty every time
            # unless you persist it (no volume on Redis this phase — deliberate).
            redis_client.set("hit_count", 1)
            count = 1
        else:
            # Key exists — increment it.
            # incr() is atomic — safe even with concurrent requests.
            count = redis_client.incr("hit_count")

        return {"cache": "connected", "hit_count": int(count)}
    except Exception as e:
        return {"cache": "error", "detail": str(e)}, 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
