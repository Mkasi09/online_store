import random
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("db.sqlite3")
BACKUP_PATH = Path("db.sqlite3.bak")
TOTAL_REVIEWS = 4500


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Could not find {DB_PATH} in the current directory.")

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backed up {DB_PATH} -> {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rng = random.Random(20261124)

    sa_first_names = [
        "Thabo", "Sipho", "Lerato", "Naledi", "Kagiso", "Ayanda", "Zanele", "Bongani",
        "Lindiwe", "Mpho", "Tshepo", "Refilwe", "Sibusiso", "Karabo", "Palesa", "Mandla",
        "Nthabiseng", "Andile", "Busisiwe", "Katlego", "Jabu", "Nomsa", "Vusi", "Khanyi",
        "Tumelo", "Zinhle", "Sello", "Boitumelo", "Lwazi", "Dineo", "Thabiso", "Amahle",
        "Kgothatso", "Precious", "Rethabile", "Siyabonga", "Masego", "Tshiamo", "Nhlanhla", "Mbali",
        "Pieter", "Annelize", "Hendrik", "Mariska", "Willem", "Chanelle", "Jacques", "Zandri",
        "Rohan", "Priya", "Kiran", "Anushka", "Devendra", "Meera", "Yusuf", "Fatima",
        "Amina", "Tariq", "Zaid", "Aisha", "Keanu", "Talia", "Brandon", "Chantelle",
        "Kabelo", "Onalenna", "Lesedi", "Tebogo", "Neo", "Kamohelo", "Koketso", "Oarabile",
        "Lwandle", "Phumlani", "Nosipho", "Zukiswa", "Bulelwa", "Sakhile", "Sphesihle", "Nokuthula",
        "Hlengiwe", "Thandeka", "Wandile", "Mthokozisi", "Philani", "Lungelo", "Asanda", "Sinazo",
        "Olebogeng", "Reabetswe", "Keabetswe", "Tlotlo", "Bokamoso", "Mphoentle", "Dimpho", "Gontse",
        "Khululiwe", "Nontobeko", "Bandile", "Sandile", "Nkosinathi", "Lindokuhle", "Ayabonga", "Anele",
    ]

    sa_surnames = [
        "Mokoena", "Dlamini", "Nkosi", "Ndlovu", "Khumalo", "Mahlangu", "Mabena", "Molefe",
        "Mthembu", "Sithole", "Zwane", "Zulu", "Bhengu", "Buthelezi", "Shabalala", "Maseko",
        "Modise", "Tshabalala", "Mnguni", "Khoza", "Ngubane", "Radebe", "Masilela", "Mkhize",
        "Cele", "Gcabashe", "Hlatshwayo", "Magagula", "Mahlobo", "Mathebula", "Mhlongo",
        "Naidoo", "Pillay", "Govender", "Chetty", "Reddy", "Patel", "Maharaj", "Singh",
        "Botha", "Venter", "Pretorius", "Van der Merwe", "Coetzee", "Nel", "Fourie", "Du Plessis",
        "Jacobs", "Williams", "Petersen", "Solomons", "Adams", "Jansen", "Steyn", "Louw",
        "Omar", "Hassan", "Ismail", "Abrahams", "Davids", "Hendricks", "October", "Maluleke",
        "Chauke", "Baloyi", "Nwosu", "Mabunda", "Shibambu", "Ngwenya", "Tshivhase", "Maphosa",
        "Ramaphosa", "Motlanthe", "Zuma", "Mbeki", "Sisulu", "Tutu", "Mandela", "Biko",
        "Ngcobo", "Mazibuko", "Hadebe", "Kunene", "Xulu", "Zungu", "Mbonambi", "Ntanzi",
    ]

    fn_uniq = list(dict.fromkeys(sa_first_names))
    ln_uniq = list(dict.fromkeys(sa_surnames))
    pairs = [(fn, ln) for fn in fn_uniq for ln in ln_uniq]
    rng.shuffle(pairs)
    selected_pairs = pairs[:TOTAL_REVIEWS]

    existing_pw = cur.execute("SELECT password FROM auth_user WHERE password != '' LIMIT 1").fetchone()
    sample_pw = existing_pw[0] if existing_pw else "pbkdf2_sha256$600000$placeholder$hash"

    used_usernames = {r[0] for r in cur.execute("SELECT username FROM auth_user").fetchall()}
    base_date = datetime(2026, 3, 18, 10, 0, 0)

    user_rows = []
    for idx, (fn, ln) in enumerate(selected_pairs, start=1):
        base_un = f"{fn.lower()}.{ln.lower().replace(' ', '')}"
        username = base_un
        suffix = 1
        while username in used_usernames:
            suffix += 1
            username = f"{base_un}{suffix}"
        used_usernames.add(username)

        email = f"{username}@example.co.za"
        joined = (base_date + timedelta(minutes=idx * 8)).strftime("%Y-%m-%d %H:%M:%S.%f")
        user_rows.append((
            sample_pw,
            None,
            0,
            username,
            ln,
            email,
            0,
            1,
            joined,
            fn,
        ))

    cur.executemany(
        """
        INSERT INTO auth_user (
            password, last_login, is_superuser, username, last_name,
            email, is_staff, is_active, date_joined, first_name
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        user_rows,
    )

    new_users = cur.execute(
        f"SELECT id FROM auth_user ORDER BY id DESC LIMIT {TOTAL_REVIEWS}"
    ).fetchall()
    new_user_ids = [row[0] for row in reversed(new_users)]

    active_products = cur.execute(
        """
        SELECT p.id, m.name, c.name, p.storage, p.condition
        FROM store_iphoneproduct p
        JOIN store_iphonemodel m ON p.iphone_model_id = m.id
        JOIN store_color c ON p.color_id = c.id
        WHERE p.is_active = 1
        ORDER BY p.id
        """
    ).fetchall()

    n_prods = len(active_products)
    counts = [2] * n_prods
    remaining = TOTAL_REVIEWS - sum(counts)

    weights = []
    for _, model_name, _, _, cond in active_products:
        w = 1.0
        if any(gen in model_name for gen in ("17", "16", "15", "14")):
            w += 1.5
        if "Pro" in model_name:
            w += 0.5
        if cond == "new":
            w += 0.5
        weights.append(w)

    indices = list(range(n_prods))
    while remaining > 0:
        candidates = [i for i in indices if counts[i] < 10] or indices
        chosen_weights = [weights[i] for i in candidates]
        picked = rng.choices(candidates, weights=chosen_weights, k=1)[0]
        counts[picked] += 1
        remaining -= 1

    good_comments = [
        "Sharp phone, delivery to Joburg was super fast and battery health is solid.",
        "Very happy with this {model} ({storage}). Screen is crisp and Face ID works fast.",
        "Clean device with zero scratches. Arrived well-packaged in Cape Town within two days.",
        "Great value for money in South Africa. Camera quality in low light is impressive.",
        "Smooth performance all day, even with heavy WhatsApp, banking apps, and maps.",
        "Pleasantly surprised by the condition. Charging is quick and speakers are loud and clear.",
        "Bought this for work and daily use—snappy, reliable, and network reception is strong.",
        "Awesome upgrade! The {color} finish looks clean and the battery easily lasts a full day.",
        "Everything works as expected out of the box. Smooth checkout and helpful support.",
        "Solid build quality and great display. Definitely recommend if you want a dependable iPhone.",
    ]

    lower_comments = [
        "Battery drains a bit quicker than I hoped when using mobile data all day.",
        "Phone works fine overall, but courier delivery took longer than estimated.",
        "Price is fair, though I noticed minor warmth during extended camera use.",
        "Decent everyday phone, nothing extraordinary, and expected slightly better battery life.",
        "Had to top up charging more often than expected when travelling, otherwise usable.",
    ]

    # 80% good (3,600) and 20% lower-rated (900) out of 4,500 reviews
    good_target = int(TOTAL_REVIEWS * 0.80)
    lower_target = TOTAL_REVIEWS - good_target
    sentiment_pool = ["good"] * good_target + ["lower"] * lower_target
    rng.shuffle(sentiment_pool)

    review_rows = []
    u_idx = 0
    s_idx = 0

    for (prod_id, model_name, color_name, storage, _), rev_count in zip(active_products, counts):
        for _ in range(rev_count):
            kind = sentiment_pool[s_idx]
            s_idx += 1
            user_id = new_user_ids[u_idx]
            u_idx += 1

            if kind == "good":
                rating = rng.choices([5, 4], weights=[0.75, 0.25], k=1)[0]
                template = rng.choice(good_comments)
            else:
                rating = rng.choices([3, 2, 1], weights=[0.50, 0.30, 0.20], k=1)[0]
                template = rng.choice(lower_comments)

            comment = template.format(model=model_name, storage=storage, color=color_name)
            verified = 1 if rng.random() < 0.85 else 0
            created = base_date + timedelta(
                days=rng.randint(5, 245),
                minutes=rng.randint(0, 1439),
                seconds=rng.randint(0, 59),
            )
            ts = created.strftime("%Y-%m-%d %H:%M:%S.%f")

            review_rows.append((
                rating,
                comment,
                "approved",
                verified,
                ts,
                ts,
                prod_id,
                user_id,
            ))

    cur.executemany(
        """
        INSERT INTO store_productreview (
            rating, comment, status, verified_purchase,
            created_at, updated_at, product_id, user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        review_rows,
    )

    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM store_productreview").fetchone()[0]
    good_cnt = cur.execute("SELECT COUNT(*) FROM store_productreview WHERE rating >= 4").fetchone()[0]
    covered_phones = cur.execute("SELECT COUNT(DISTINCT product_id) FROM store_productreview").fetchone()[0]
    conn.close()

    print(f"Done. Inserted {total} reviews across {covered_phones} active phones ({good_cnt}/{total} >= 4 stars).")


if __name__ == "__main__":
    main()
