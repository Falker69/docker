"""
Бэкенд лабораторной работы (вариант 18 - онлайн-переводчик).

Задачи:
  * дать фронтенду REST API поверх PostgreSQL (CRUD по истории переводов);
  * ходить в отдельный web-сервис-переводчик;
  * связывать эти две вещи между собой.

Эндпоинты:
  GET    /api/health
  GET    /api/languages
  GET    /api/vocabulary
  POST   /api/translate
  GET    /api/history
  DELETE /api/history
"""

import os
import time

import requests
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

# берём настройки из окружения; дефолты - чтобы можно было запустить локально
DB_DSN = os.getenv(
    "DATABASE_URL",
    "host=db port=5432 dbname=translator_db user=postgres password=postgres",
)
TRANSLATOR_URL = os.getenv("WEB_SERVICE_URL", "http://web-service:5001")

app = Flask(__name__)

# Postgres поднимается не сразу, поэтому ждём его в цикле
pool = None
for i in range(60):
    try:
        pool = SimpleConnectionPool(1, 10, dsn=DB_DSN)
        print("[backend] подключились к БД")
        break
    except Exception as e:
        print(f"[backend] БД ещё не готова ({i + 1}/60): {e}")
        time.sleep(2)

if pool is None:
    raise RuntimeError("не удалось подключиться к базе за 2 минуты")


def db_query(sql, params=None, fetch=True, commit=False):
    """Один запрос через пул соединений."""
    conn = pool.getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(sql, params)
            rows = cur.fetchall() if fetch else None
        finally:
            cur.close()
        if commit:
            conn.commit()
        return rows
    finally:
        pool.putconn(conn)


@app.get("/api/health")
def health():
    try:
        db_query("SELECT 1")
    except Exception as e:
        return jsonify({"status": "degraded", "db": str(e)}), 503
    return jsonify({"status": "ok", "db": "ok"}), 200


@app.get("/api/languages")
def languages():
    try:
        r = requests.get(f"{TRANSLATOR_URL}/languages", timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.RequestException as e:
        return jsonify({"error": f"web-сервис не ответил: {e}"}), 502


@app.get("/api/vocabulary")
def vocabulary():
    try:
        r = requests.get(f"{TRANSLATOR_URL}/vocabulary", timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.RequestException as e:
        return jsonify({"error": f"web-сервис не ответил: {e}"}), 502


@app.post("/api/translate")
def translate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    target_lang = (data.get("target_lang") or "").lower()

    if not text:
        return jsonify({"error": "поле text обязательно"}), 400
    if not target_lang:
        return jsonify({"error": "поле target_lang обязательно"}), 400

    # дёргаем web-сервис переводчика
    try:
        r = requests.post(
            f"{TRANSLATOR_URL}/translate",
            json={"text": text, "target_lang": target_lang},
            timeout=15,
        )
        r.raise_for_status()
        result = r.json()
    except requests.RequestException as e:
        return jsonify({"error": f"web-сервис не ответил: {e}"}), 502

    # сохраняем в историю
    row = db_query(
        """
        INSERT INTO translations (original_text, translated_text, source_lang, target_lang)
        VALUES (%s, %s, %s, %s)
        RETURNING id, original_text, translated_text, source_lang, target_lang, created_at
        """,
        (
            result["original_text"],
            result["translated_text"],
            result["source_lang"],
            result["target_lang"],
        ),
        commit=True,
    )[0]

    return jsonify({
        "id": row["id"],
        "original_text": row["original_text"],
        "translated_text": row["translated_text"],
        "source_lang": row["source_lang"],
        "target_lang": row["target_lang"],
        "created_at": row["created_at"].isoformat(),
        "engine": result.get("engine", "unknown"),
    }), 201


@app.get("/api/history")
def history():
    limit = min(int(request.args.get("limit", 50)), 200)
    rows = db_query(
        """
        SELECT id, original_text, translated_text, source_lang, target_lang, created_at
        FROM translations
        ORDER BY created_at DESC, id DESC
        LIMIT %s
        """,
        (limit,),
    )
    return jsonify({
        "count": len(rows),
        "items": [
            {**row, "created_at": row["created_at"].isoformat()} for row in rows
        ],
    })


@app.delete("/api/history")
def clear_history():
    record_id = request.args.get("id", type=int)
    if record_id is not None:
        db_query(
            "DELETE FROM translations WHERE id = %s",
            (record_id,),
            fetch=False,
            commit=True,
        )
        return jsonify({"status": "ok", "deleted_id": record_id}), 200
    db_query("DELETE FROM translations", fetch=False, commit=True)
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)