import random
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path("db.sqlite3")
BACKUP_PATH = Path("db.sqlite3.bak")
TOTAL_REVIEWS = 4500


def make_natural_review(rng: random.Random, kind: str, rating: int,
                        model: str, color: str, storage: str, condition: str) -> str:
    """
    Generate varied, natural-sounding reviews with different sentence structures,
    lengths, tones, punctuation styles, and casual/detailed phrasing—without
    robotic tags or identical boilerplate templates.
    """
    is_new = condition == "new"
    c_lower = color.lower()
    m_short = model.replace("iPhone ", "")

    good_4500 = [
        # Short / punchy
        f"Got {model} ({storage}) yesterday, super clean and fast.",
        f"Love this {c_lower} {model}. Screen and camera are top notch.",
        f"No complaints at all, {storage} is plenty for me.",
        f"Came in great shape. Battery lasts me through the day easily.",
        f"Best phone upgrade I have made in a while.",
        f"Smooth as butter on {model}, zero lag so far.",
        f"Really digging the {c_lower} colour on this one.",
        f"Arrived quickly and works just like it should.",
        f"Clean unit, fair price, happy customer.",
        f"Face ID and cameras are quick, very happy with it.",

        # Medium / conversational SA phrasing
        f"Ordered the {storage} {model} in {c_lower} and it arrived in Joburg in two days. Looks practically untouched and runs smoothly.",
        f"I was a bit nervous buying online but the {model} came well packed and battery life has been solid all week.",
        f"Using it mostly for WhatsApp, Capitec, Instagram and maps. No hiccups at all and the {c_lower} finish looks smart.",
        f"Picked up the {model} {storage} for varsity and daily use. Display is crisp and sound is clear.",
        f"Switched over without any stress. Data transfer took a few minutes and everything on the phone feels snappy.",
        f"Took it to Durban over the weekend and took loads of photos. Quality came out really clean.",
        f"Honestly better condition than I expected. Frame and glass look clean and charging is fast.",
        f"Great everyday phone. Doesn't overheat on me and gets me from morning till night.",
        f"Happy with the {c_lower} {model}. Good value compared to what other places charge.",
        f"Bought this for work calls, emails and navigation. Handles everything smoothly.",

        # Slightly more detailed / specific
        f"Been using the {storage} {model} ({c_lower}) for about two weeks now. Battery easily gets me through a full day of moderate to heavy use, and the camera holds up well indoors too.",
        f"Delivery to Pretoria was right on time. The {model} had no noticeable marks on the body, speakers are loud enough, and apps open right away.",
        f"Needed something reliable for business calls and banking on the move. This {c_lower} {model} with {storage} has been consistent every day.",
        f"The OLED screen looks sharp watching series at night, and {storage} gives me breathing room for photos and videos without stressing about space.",
        f"Came neatly boxed with no drama. Tested the cameras, mic, speakers and charging port on day one—everything works properly.",
        f"Coming from an older phone, the speed difference on {model} is night and day. Very pleased with how it performs.",
        f"Nice weight in the hand and the {c_lower} shade stands out without being loud. Happy I went with {storage}.",
        f"Used it non-stop on a road trip to Nelspruit using Google Maps and Spotify. Battery held up way better than my old phone.",
        f"Solid buy overall. Pricing made sense for {storage} and the phone feels genuine and well kept.",
        f"Smooth checkout, quick dispatch to Cape Town, and the {model} works great out of the box.",
    ]

    lower_123 = [
        # Mild / 3-star realistic notes
        f"It's okay overall, just wish the battery lasted a bit longer on mobile data.",
        f"Phone works fine for calls and WhatsApp, though delivery took an extra day or two.",
        f"Decent enough for the price, gets slightly warm when I use the camera for a while.",
        f"Not bad at all, just expected slightly stronger battery backup during busy days.",
        f"Good screen and camera, battery is average if you're out all day without a charger.",
        f"Works as expected most of the time, had one slow moment when updating apps.",
        f"Fair deal for {storage}, battery life is alright but nothing crazy.",
        f"Happy enough with the {c_lower} {model}, just have to top up the battery in the late afternoon.",
        f"Courier took slightly longer than estimated to reach me, otherwise the phone is fine.",
        f"Does the job for everyday tasks, though I expected a bit more battery endurance.",

        # Stronger 1-2 star realistic complaints
        f"Battery drops quicker than I hoped when using data and maps. Have to carry a power bank.",
        f"A bit disappointed with delivery timing—took longer than expected and tracking wasn't super clear.",
        f"Gets noticeably warm when charging and browsing at the same time.",
        f"Battery health/endurance feels underwhelming for how much I use my phone daily.",
        f"Expected better battery life on this {model}. Fine around the house, less so when out.",
        f"Took longer to arrive than I wanted, which was frustrating since I needed it urgently.",
        f"Decent look and feel, but battery drains faster than I'd like on heavy days.",
        f"Not terrible, just average—battery needs a mid-day charge if I'm on social media a lot.",
    ]

    # Expand pool with natural variations so no two reviews feel like cloned lines
    extra_good = []
    cities = ["Joburg", "Cape Town", "Durban", "Pretoria", "Mbombela", "Polokwane", "Gqeberha", "Bloemfontein", "Sandton", "Centurion"]
    for i, base in enumerate(good_4500):
        city = cities[i % len(cities)]
        extra_good.append(base)
        extra_good.append(f"{base} Delivered to {city}.")
        if not is_new:
            extra_good.append(f"Pre-owned {m_short} in {c_lower} ({storage}): {base[0].lower() + base[1:]}")
        else:
            extra_good.append(f"Brand new {m_short} {storage} in {c_lower} — {base[0].lower() + base[1:]}")

    extra_lower = []
    for i, base in enumerate(lower_123):
        city = cities[i % len(cities)]
        extra_lower.append(base)
        extra_lower.append(f"{base} ({city} delivery)")
        extra_lower.append(f"{m_short} {storage} ({c_lower}): {base[0].lower() + base[1:]}")

    pool = extra_good if kind == "good" else extra_lower
    chosen = rng.choice(pool)

    # Subtle human touches: occasional lowercase start, extra exclamation, or tiny trailing note
    roll = rng.random()
    if roll < 0.12 and len(chosen) > 15:
        chosen = chosen[0].lower() + chosen[1:]
    elif roll < 0.22 and kind == "good" and not chosen.endswith("!"):
        chosen = chosen.rstrip(".") + "!"

    return chosen


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Could not find {DB_PATH} in the current directory.")

    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Backed up {DB_PATH} -> {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    rng = random.Random(20261124)

    deleted_count = cur.execute("DELETE FROM store_productreview").rowcount
    print(f"Deleted {deleted_count} existing review(s) from store_productreview.")

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

    good_target = int(TOTAL_REVIEWS * 0.80)
    lower_target = TOTAL_REVIEWS - good_target
    sentiment_pool = ["good"] * good_target + ["lower"] * lower_target
    rng.shuffle(sentiment_pool)

    review_rows = []
    u_idx = 0
    s_idx = 0

    for (prod_id, model_name, color_name, storage, cond), rev_count in zip(active_products, counts):
        for _ in range(rev_count):
            kind = sentiment_pool[s_idx]
            s_idx += 1
            user_id = new_user_ids[u_idx]
            u_idx += 1

            rating = (
                rng.choices([5, 4], weights=[0.75, 0.25], k=1)[0]
                if kind == "good"
                else rng.choices([3, 2, 1], weights=[0.50, 0.30, 0.20], k=1)[0]
            )

            comment = make_natural_review(
                rng, kind, rating, model_name, color_name, storage, cond
            )
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

    print(
        f"Done. Inserted {total} reviews across {covered_phones} active phones "
        f"({good_cnt}/{total} >= 4 stars)."
    )


if __name__ == "__main__":
    main()
