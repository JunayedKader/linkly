import os
from flask import Flask

app = Flask(__name__)

APP_ENV = os.environ.get("APP_ENV", "development")

@app.route("/")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
