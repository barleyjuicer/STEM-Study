import csv
import json
import math
import os
import random
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parents[1]


def portable_root():
    configured_root = os.environ.get("STEM_STUDY_PORTABLE_DIR")
    if configured_root:
        return Path(configured_root)
    return PROJECT_ROOT


PORTABLE_ROOT = portable_root()
DATA_DIR = PORTABLE_ROOT / "data"
EXPORTS_DIR = PORTABLE_ROOT / "exports"
REPORTS_DIR = PORTABLE_ROOT / "reports"
DB_PATH = DATA_DIR / "stem_study.db"

PHYSICS_TOPICS = [
    "Coulomb's Law",
    "Electric Field",
    "Electric Potential",
    "Ohm's Law",
    "Series Circuits",
    "Parallel Circuits",
    "Magnetic Force",
    "Lens Equation",
    "Mirror Equation",
]

CRYPTO_TOPICS = [
    "Modular arithmetic",
    "Greatest common divisor using Euclidean algorithm",
    "Modular inverse",
    "Caesar cipher",
    "Affine cipher",
    "Vigenere cipher",
    "Toy RSA key generation",
    "Toy RSA encryption/decryption",
]

DIFFICULTIES = ["Easy", "Medium", "Hard"]
SUBJECT_TOPICS = {"Physics II": PHYSICS_TOPICS, "Intro Cryptography": CRYPTO_TOPICS}


def connect_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS problem_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            generator_key TEXT NOT NULL,
            answer_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            mode TEXT NOT NULL,
            prompt TEXT NOT NULL,
            generated_data TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            answer_type TEXT NOT NULL,
            tolerance_percent REAL,
            units TEXT,
            formula TEXT,
            worked_solution TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attempt_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL,
            student_answer TEXT NOT NULL,
            show_work TEXT,
            is_correct INTEGER NOT NULL,
            confidence INTEGER,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(attempt_id) REFERENCES generated_attempts(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS student_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            correct INTEGER NOT NULL DEFAULT 0,
            avg_confidence REAL,
            updated_at TEXT NOT NULL,
            UNIQUE(subject, topic, difficulty)
        )
        """
    )
    seed_templates(cur)
    conn.commit()
    conn.close()


def seed_templates(cur):
    cur.execute("SELECT COUNT(*) FROM problem_templates")
    if cur.fetchone()[0] > 0:
        return
    now = datetime.now().isoformat(timespec="seconds")
    rows = []
    for subject, topics in SUBJECT_TOPICS.items():
        for topic in topics:
            for difficulty in DIFFICULTIES:
                answer_type = "numeric" if subject == "Physics II" else "exact"
                rows.append((subject, topic, difficulty, make_generator_key(subject, topic), answer_type, now))
    cur.executemany(
        """
        INSERT INTO problem_templates
        (subject, topic, difficulty, generator_key, answer_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def make_generator_key(subject, topic):
    return f"{subject.lower().replace(' ', '_')}:{topic.lower().replace(' ', '_')}"


def sci(value, digits=3):
    return f"{value:.{digits}g}"


def difficulty_scale(difficulty):
    return {"Easy": 1, "Medium": 2, "Hard": 3}[difficulty]


def make_problem(subject, topic, difficulty):
    generators = {
        ("Physics II", "Coulomb's Law"): gen_coulomb,
        ("Physics II", "Ohm's Law"): gen_ohms_law,
        ("Physics II", "Series Circuits"): gen_series_circuit,
        ("Physics II", "Electric Field"): gen_electric_field,
        ("Physics II", "Electric Potential"): gen_electric_potential,
        ("Physics II", "Parallel Circuits"): gen_parallel_circuit,
        ("Physics II", "Magnetic Force"): gen_magnetic_force,
        ("Physics II", "Lens Equation"): gen_lens_equation,
        ("Physics II", "Mirror Equation"): gen_mirror_equation,
        ("Intro Cryptography", "Modular arithmetic"): gen_modular_arithmetic,
        ("Intro Cryptography", "Greatest common divisor using Euclidean algorithm"): gen_gcd,
        ("Intro Cryptography", "Modular inverse"): gen_mod_inverse,
        ("Intro Cryptography", "Caesar cipher"): gen_caesar,
        ("Intro Cryptography", "Affine cipher"): gen_affine,
        ("Intro Cryptography", "Vigenere cipher"): gen_vigenere,
        ("Intro Cryptography", "Toy RSA key generation"): gen_rsa_keygen,
        ("Intro Cryptography", "Toy RSA encryption/decryption"): gen_rsa_encrypt_decrypt,
    }
    # To add a generator later: write a gen_* function that returns the same
    # dictionary shape, then add it to this mapping and the topic list above.
    return generators[(subject, topic)](difficulty)


def gen_coulomb(difficulty):
    k = 8.99e9
    scale = difficulty_scale(difficulty)
    q1_uc = random.randint(1, 5 * scale)
    q2_uc = random.randint(1, 6 * scale)
    r = random.choice([0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]) / (1 if scale < 3 else 1.25)
    force = k * (q1_uc * 1e-6) * (q2_uc * 1e-6) / (r**2)
    return numeric_problem(
        "Physics II",
        "Coulomb's Law",
        difficulty,
        f"Two point charges, q1 = {q1_uc} microC and q2 = {q2_uc} microC, are {r:.2f} m apart. What is the magnitude of the electric force between them?",
        force,
        "N",
        "F = k|q1 q2| / r^2",
        [
            f"Convert charges: q1 = {q1_uc} x 10^-6 C, q2 = {q2_uc} x 10^-6 C.",
            f"Substitute: F = (8.99 x 10^9)({q1_uc} x 10^-6)({q2_uc} x 10^-6) / ({r:.2f})^2.",
            f"Calculate: F = {sci(force)} N.",
        ],
        {"q1_micro_c": q1_uc, "q2_micro_c": q2_uc, "r_m": r},
    )


def gen_ohms_law(difficulty):
    scale = difficulty_scale(difficulty)
    current = random.choice([0.25, 0.5, 0.75, 1.2, 1.5, 2.0, 2.5]) * scale
    resistance = random.choice([4, 6, 8, 10, 12, 15, 20])
    voltage = current * resistance
    return numeric_problem(
        "Physics II",
        "Ohm's Law",
        difficulty,
        f"A resistor has resistance R = {resistance} ohms and current I = {current:g} A. What voltage is across it?",
        voltage,
        "V",
        "V = IR",
        [
            f"Use Ohm's Law: V = IR.",
            f"Substitute: V = ({current:g} A)({resistance} ohms).",
            f"Calculate: V = {sci(voltage)} V.",
        ],
        {"current_a": current, "resistance_ohm": resistance},
    )


def gen_series_circuit(difficulty):
    count = 2 + (difficulty_scale(difficulty) > 1)
    resistors = [random.randint(2, 12) * 5 for _ in range(count)]
    voltage = random.choice([6, 9, 12, 18, 24])
    total_r = sum(resistors)
    current = voltage / total_r
    return numeric_problem(
        "Physics II",
        "Series Circuits",
        difficulty,
        f"Resistors {', '.join(str(r) for r in resistors)} ohms are connected in series to a {voltage} V battery. What is the circuit current?",
        current,
        "A",
        "R_total = R1 + R2 + ... and I = V / R_total",
        [
            f"Add series resistors: R_total = {' + '.join(str(r) for r in resistors)} = {total_r} ohms.",
            f"Use I = V / R_total = {voltage} / {total_r}.",
            f"Calculate: I = {sci(current)} A.",
        ],
        {"resistors_ohm": resistors, "voltage_v": voltage},
    )


def gen_electric_field(difficulty):
    force = random.choice([0.02, 0.05, 0.08, 0.12, 0.2]) * difficulty_scale(difficulty)
    charge_uc = random.randint(1, 9)
    field = force / (charge_uc * 1e-6)
    return numeric_problem("Physics II", "Electric Field", difficulty, f"A {charge_uc} microC test charge feels a force of {force:g} N. What is the electric field magnitude?", field, "N/C", "E = F / q", [f"Convert q = {charge_uc} x 10^-6 C.", f"E = {force:g} / ({charge_uc} x 10^-6).", f"E = {sci(field)} N/C."], {"force_n": force, "charge_micro_c": charge_uc})


def gen_electric_potential(difficulty):
    energy = random.choice([0.012, 0.025, 0.05, 0.10]) * difficulty_scale(difficulty)
    charge_mc = random.choice([1, 2, 4, 5])
    voltage = energy / (charge_mc * 1e-3)
    return numeric_problem("Physics II", "Electric Potential", difficulty, f"Moving a {charge_mc} mC charge requires {energy:g} J of work. What potential difference is required?", voltage, "V", "V = W / q", [f"Convert q = {charge_mc} x 10^-3 C.", f"V = {energy:g} / ({charge_mc} x 10^-3).", f"V = {sci(voltage)} V."], {"energy_j": energy, "charge_mc": charge_mc})


def gen_parallel_circuit(difficulty):
    r1 = random.choice([6, 8, 10, 12, 15, 20])
    r2 = random.choice([6, 8, 10, 12, 15, 20])
    eq = 1 / (1 / r1 + 1 / r2)
    return numeric_problem("Physics II", "Parallel Circuits", difficulty, f"Two resistors, {r1} ohms and {r2} ohms, are connected in parallel. What is the equivalent resistance?", eq, "ohms", "1/R_eq = 1/R1 + 1/R2", [f"Use 1/R_eq = 1/{r1} + 1/{r2}.", f"1/R_eq = {sci(1/r1 + 1/r2)}.", f"R_eq = {sci(eq)} ohms."], {"r1_ohm": r1, "r2_ohm": r2})


def gen_magnetic_force(difficulty):
    charge_uc = random.randint(1, 8)
    speed = random.choice([1.5e5, 2.0e5, 3.0e5, 4.0e5]) * difficulty_scale(difficulty)
    field = random.choice([0.10, 0.20, 0.35, 0.50])
    force = charge_uc * 1e-6 * speed * field
    return numeric_problem("Physics II", "Magnetic Force", difficulty, f"A {charge_uc} microC charge moves perpendicular to a {field:g} T magnetic field at {sci(speed)} m/s. What magnetic force acts on it?", force, "N", "F = qvB sin(theta), with theta = 90 degrees", [f"Since motion is perpendicular, sin(90 degrees) = 1.", f"F = ({charge_uc} x 10^-6)({sci(speed)})({field:g}).", f"F = {sci(force)} N."], {"charge_micro_c": charge_uc, "speed_m_s": speed, "field_t": field})


def gen_lens_equation(difficulty):
    f = random.choice([10, 12, 15, 20])
    do = random.choice([25, 30, 40, 60])
    di = 1 / (1 / f - 1 / do)
    return numeric_problem("Physics II", "Lens Equation", difficulty, f"A thin converging lens has focal length {f} cm. An object is {do} cm from the lens. What is the image distance?", di, "cm", "1/f = 1/do + 1/di", [f"Solve for image distance: 1/di = 1/f - 1/do.", f"1/di = 1/{f} - 1/{do}.", f"di = {sci(di)} cm."], {"focal_length_cm": f, "object_distance_cm": do})


def gen_mirror_equation(difficulty):
    f = random.choice([8, 10, 12, 15])
    do = random.choice([20, 24, 30, 45])
    di = 1 / (1 / f - 1 / do)
    return numeric_problem("Physics II", "Mirror Equation", difficulty, f"A concave mirror has focal length {f} cm. An object is {do} cm from the mirror. What is the image distance?", di, "cm", "1/f = 1/do + 1/di", [f"Rearrange: 1/di = 1/f - 1/do.", f"1/di = 1/{f} - 1/{do}.", f"di = {sci(di)} cm."], {"focal_length_cm": f, "object_distance_cm": do})


def numeric_problem(subject, topic, difficulty, prompt, answer, units, formula, steps, data):
    return {
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "prompt": prompt,
        "answer_type": "numeric",
        "correct_answer": answer,
        "display_answer": f"{sci(answer)} {units}",
        "tolerance_percent": 2.0,
        "units": units,
        "formula": formula,
        "worked_solution": "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps)),
        "data": data,
        "choices": [],
    }


def gen_modular_arithmetic(difficulty):
    scale = difficulty_scale(difficulty)
    a = random.randint(20, 80 * scale)
    b = random.randint(10, 60 * scale)
    m = random.choice([5, 7, 11, 13, 17, 19])
    value = (a + b) % m
    return exact_problem(
        "Intro Cryptography",
        "Modular arithmetic",
        difficulty,
        f"Compute ({a} + {b}) mod {m}.",
        value,
        [f"Add first: {a} + {b} = {a + b}.", f"Divide by {m} and keep the remainder.", f"{a + b} mod {m} = {value}."],
        {"a": a, "b": b, "modulus": m},
    )


def gen_gcd(difficulty):
    a = random.randint(35, 180 * difficulty_scale(difficulty))
    b = random.randint(20, a - 1)
    g = math.gcd(a, b)
    steps = euclid_steps(a, b)
    return exact_problem("Intro Cryptography", "Greatest common divisor using Euclidean algorithm", difficulty, f"Use the Euclidean algorithm to find gcd({a}, {b}).", g, steps + [f"The last nonzero remainder is {g}, so gcd({a}, {b}) = {g}."], {"a": a, "b": b})


def gen_mod_inverse(difficulty):
    moduli = [11, 17, 19, 23, 29, 31]
    m = random.choice(moduli)
    a = random.randint(2, m - 2)
    while math.gcd(a, m) != 1:
        a = random.randint(2, m - 2)
    inv = pow(a, -1, m)
    return exact_problem("Intro Cryptography", "Modular inverse", difficulty, f"Find the modular inverse of {a} modulo {m}.", inv, [f"We need x such that {a}x = 1 mod {m}.", f"Testing or using extended Euclid gives x = {inv}.", f"Check: ({a} x {inv}) mod {m} = {(a * inv) % m}."], {"a": a, "modulus": m})


def gen_caesar(difficulty):
    words = ["MATH", "VECTOR", "CIPHER", "STUDY", "FIELD"]
    text = random.choice(words)
    shift = random.randint(1, 9)
    cipher = caesar_shift(text, shift)
    return text_problem("Intro Cryptography", "Caesar cipher", difficulty, f"Encrypt {text} with a Caesar shift of {shift}.", cipher, [f"Shift each letter forward by {shift}.", f"{text} becomes {cipher}."], {"plaintext": text, "shift": shift})


def gen_affine(difficulty):
    text = random.choice(["CAT", "DOG", "SUN", "MAP"])
    a = random.choice([3, 5, 7, 11])
    b = random.randint(1, 9)
    cipher = "".join(chr(((a * (ord(ch) - 65) + b) % 26) + 65) for ch in text)
    return text_problem("Intro Cryptography", "Affine cipher", difficulty, f"Encrypt {text} using affine cipher E(x)=({a}x + {b}) mod 26, where A=0.", cipher, [f"Convert letters to numbers with A=0.", f"Apply E(x)=({a}x + {b}) mod 26 to each letter.", f"The ciphertext is {cipher}."], {"plaintext": text, "a": a, "b": b})


def gen_vigenere(difficulty):
    text = random.choice(["MATH", "CODE", "DATA"])
    key = random.choice(["KEY", "CAT", "SUN"])
    cipher_chars = []
    steps = []
    for i, ch in enumerate(text):
        shift = ord(key[i % len(key)]) - 65
        out = chr(((ord(ch) - 65 + shift) % 26) + 65)
        cipher_chars.append(out)
        steps.append(f"{ch} shifted by {key[i % len(key)]} ({shift}) gives {out}.")
    cipher = "".join(cipher_chars)
    return text_problem("Intro Cryptography", "Vigenere cipher", difficulty, f"Encrypt {text} using Vigenere key {key}. Use A=0 shifts.", cipher, steps + [f"The ciphertext is {cipher}."], {"plaintext": text, "key": key})


def gen_rsa_keygen(difficulty):
    p, q = random.choice([(5, 11), (7, 11), (7, 13), (11, 13)])
    n = p * q
    phi = (p - 1) * (q - 1)
    e = random.choice([x for x in [3, 5, 7, 11, 13] if math.gcd(x, phi) == 1])
    d = pow(e, -1, phi)
    return exact_problem("Intro Cryptography", "Toy RSA key generation", difficulty, f"For toy RSA with p={p}, q={q}, and e={e}, find the private exponent d.", d, [f"Compute n = pq = {p} x {q} = {n}.", f"Compute phi(n) = (p-1)(q-1) = {p-1} x {q-1} = {phi}.", f"Find d so ed = 1 mod phi(n): {e}d = 1 mod {phi}.", f"d = {d} because ({e} x {d}) mod {phi} = {(e * d) % phi}."], {"p": p, "q": q, "n": n, "phi": phi, "e": e})


def gen_rsa_encrypt_decrypt(difficulty):
    p, q, e = random.choice([(5, 11, 3), (7, 11, 7), (7, 13, 5)])
    n = p * q
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    m = random.randint(2, min(20, n - 1))
    c = pow(m, e, n)
    decrypted = pow(c, d, n)
    return exact_problem("Intro Cryptography", "Toy RSA encryption/decryption", difficulty, f"Toy RSA has p={p}, q={q}, e={e}. Encrypt plaintext m={m}. What ciphertext c do you get?", c, [f"n = pq = {p} x {q} = {n}.", f"phi(n) = ({p}-1)({q}-1) = {phi}.", f"d is the inverse of e modulo phi(n): d = {d}.", f"Encrypt with c = m^e mod n = {m}^{e} mod {n} = {c}.", f"Check decryption: m = c^d mod n = {c}^{d} mod {n} = {decrypted}."], {"p": p, "q": q, "n": n, "phi": phi, "e": e, "d": d, "plaintext": m})


def exact_problem(subject, topic, difficulty, prompt, answer, steps, data):
    return {
        "subject": subject,
        "topic": topic,
        "difficulty": difficulty,
        "prompt": prompt,
        "answer_type": "exact",
        "correct_answer": answer,
        "display_answer": str(answer),
        "tolerance_percent": None,
        "units": "",
        "formula": "",
        "worked_solution": "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps)),
        "data": data,
        "choices": [],
    }


def text_problem(subject, topic, difficulty, prompt, answer, steps, data):
    problem = exact_problem(subject, topic, difficulty, prompt, answer, steps, data)
    problem["answer_type"] = "text"
    return problem


def euclid_steps(a, b):
    steps = []
    x, y = a, b
    while y:
        q, r = divmod(x, y)
        steps.append(f"{x} = {q} x {y} + {r}.")
        x, y = y, r
    return steps


def caesar_shift(text, shift):
    return "".join(chr(((ord(ch) - 65 + shift) % 26) + 65) if ch.isalpha() else ch for ch in text.upper())


def parse_numeric_answer(raw):
    match = re.match(r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(.*?)\s*$", raw)
    if not match:
        return None, ""
    return float(match.group(1)), match.group(2).strip()


def normalize_unit(unit):
    return re.sub(r"[\s._-]+", "", unit.lower())


def unit_warning(expected_unit, entered_unit):
    if not entered_unit or not expected_unit:
        return None
    expected = normalize_unit(expected_unit)
    entered = normalize_unit(entered_unit)
    aliases = {
        "n": {"n", "newton", "newtons"},
        "v": {"v", "volt", "volts"},
        "a": {"a", "amp", "amps", "ampere", "amperes"},
        "ohms": {"ohm", "ohms", "omega"},
        "n/c": {"n/c", "newton/coulomb", "newtons/coulomb", "newtonpercoulomb", "newtonspercoulomb"},
        "cm": {"cm", "centimeter", "centimeters"},
    }
    accepted = aliases.get(expected, {expected})
    if entered not in accepted:
        return f"Unit warning: expected {expected_unit}, but you entered {entered_unit}. Your numeric answer was still graded."
    return None


def grade_answer(problem, student_answer):
    raw = student_answer.strip()
    if not raw:
        return False, "No answer entered.", None
    if problem["answer_type"] == "numeric":
        parsed = parse_numeric_answer(raw)
        if parsed[0] is None:
            return False, "Enter a numeric answer, with or without units.", None
        entered, entered_unit = parsed
        correct = float(problem["correct_answer"])
        tolerance = abs(correct) * (problem["tolerance_percent"] / 100)
        is_correct = abs(entered - correct) <= tolerance
        warning = unit_warning(problem["units"], entered_unit)
        return is_correct, f"Accepted range: {sci(correct - tolerance)} to {sci(correct + tolerance)} {problem['units']}.", warning
    if problem["answer_type"] == "exact":
        try:
            return int(raw) == int(problem["correct_answer"]), "Exact integer answer required.", None
        except ValueError:
            return False, "Enter an integer.", None
    normalized = "".join(raw.upper().split())
    correct_text = "".join(str(problem["correct_answer"]).upper().split())
    return normalized == correct_text, "Text answers ignore spaces and capitalization.", None


def save_attempt(problem, mode, student_answer, show_work, is_correct, confidence):
    conn = connect_db()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute(
        """
        INSERT INTO generated_attempts
        (subject, topic, difficulty, mode, prompt, generated_data, correct_answer,
         answer_type, tolerance_percent, units, formula, worked_solution, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            problem["subject"],
            problem["topic"],
            problem["difficulty"],
            mode,
            problem["prompt"],
            json.dumps(problem["data"]),
            str(problem["correct_answer"]),
            problem["answer_type"],
            problem["tolerance_percent"],
            problem["units"],
            problem["formula"],
            problem["worked_solution"],
            now,
        ),
    )
    attempt_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO attempt_answers
        (attempt_id, student_answer, show_work, is_correct, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (attempt_id, student_answer, show_work, int(is_correct), confidence, now),
    )
    update_stats(cur, problem, is_correct, confidence, now)
    conn.commit()
    conn.close()


def update_stats(cur, problem, is_correct, confidence, now):
    cur.execute(
        """
        INSERT INTO student_stats
        (subject, topic, difficulty, attempts, correct, avg_confidence, updated_at)
        VALUES (?, ?, ?, 1, ?, ?, ?)
        ON CONFLICT(subject, topic, difficulty) DO UPDATE SET
            attempts = attempts + 1,
            correct = correct + excluded.correct,
            avg_confidence = CASE
                WHEN excluded.avg_confidence IS NULL THEN student_stats.avg_confidence
                WHEN student_stats.avg_confidence IS NULL THEN excluded.avg_confidence
                ELSE ((student_stats.avg_confidence * student_stats.attempts) + excluded.avg_confidence) / (student_stats.attempts + 1)
            END,
            updated_at = excluded.updated_at
        """,
        (
            problem["subject"],
            problem["topic"],
            problem["difficulty"],
            int(is_correct),
            confidence,
            now,
        ),
    )


def attempts_rows():
    conn = connect_db()
    rows = conn.execute(
        """
        SELECT ga.id, ga.subject, ga.topic, ga.difficulty, ga.mode, ga.prompt,
               aa.student_answer, ga.correct_answer, aa.is_correct, aa.confidence,
               ga.timestamp
        FROM generated_attempts ga
        JOIN attempt_answers aa ON aa.attempt_id = ga.id
        ORDER BY ga.timestamp DESC
        """
    ).fetchall()
    conn.close()
    return rows


def summary_rows():
    conn = connect_db()
    rows = conn.execute(
        """
        SELECT subject, topic, difficulty, attempts, correct,
               ROUND(100.0 * correct / attempts, 1) AS accuracy_percent,
               ROUND(avg_confidence, 2) AS avg_confidence
        FROM student_stats
        ORDER BY subject, topic, difficulty
        """
    ).fetchall()
    conn.close()
    return rows


def rows_to_csv(rows):
    if not rows:
        return ""
    headers = rows[0].keys()
    output = []
    output.append(",".join(headers))
    for row in rows:
        output.append(",".join(csv_escape(row[h]) for h in headers))
    return "\n".join(output)


def csv_escape(value):
    text = "" if value is None else str(value)
    if any(ch in text for ch in [",", '"', "\n"]):
        return '"' + text.replace('"', '""') + '"'
    return text


def main():
    st.set_page_config(page_title="STEM Study Generator", layout="wide")
    init_db()
    st.title("STEM Study Generator")
    st.caption("Local practice and quizzes for Physics II and Intro Cryptography.")

    page = st.sidebar.radio("Go to", ["Practice Mode", "Quiz Mode", "Dashboard", "Sample Problems"])
    if page == "Practice Mode":
        practice_mode()
    elif page == "Quiz Mode":
        quiz_mode()
    elif page == "Dashboard":
        dashboard()
    else:
        sample_problems()


def subject_topic_controls(prefix, multi_topic=False):
    subject = st.selectbox("Subject", list(SUBJECT_TOPICS.keys()), key=f"{prefix}_subject")
    if multi_topic:
        topics = st.multiselect("Topics", SUBJECT_TOPICS[subject], default=[SUBJECT_TOPICS[subject][0]], key=f"{prefix}_topics")
    else:
        topics = st.selectbox("Topic", SUBJECT_TOPICS[subject], key=f"{prefix}_topic")
    difficulty = st.selectbox("Difficulty", DIFFICULTIES, key=f"{prefix}_difficulty")
    return subject, topics, difficulty


def practice_mode():
    st.header("Practice Mode")
    subject, topic, difficulty = subject_topic_controls("practice")
    count = st.number_input("Number of problems", min_value=1, max_value=20, value=5)

    if "practice_problem" not in st.session_state:
        st.session_state.practice_problem = None

    col1, col2 = st.columns([1, 1])
    if col1.button("Generate problem", type="primary"):
        st.session_state.practice_problem = make_problem(subject, topic, difficulty)
    if col2.button("Clear current problem"):
        st.session_state.practice_problem = None

    problem = st.session_state.practice_problem
    if problem:
        answer_form(problem, "Practice")
    st.info(f"Tip: keep generating until you complete your planned {count} problems.")


def answer_form(problem, mode):
    st.subheader(problem["topic"])
    st.write(problem["prompt"])
    if problem["formula"]:
        st.caption(f"Formula: {problem['formula']}")
    with st.form(f"answer_{mode}_{problem['topic']}_{problem['prompt']}"):
        if problem["answer_type"] == "numeric" and problem["units"]:
            student_answer = st.text_input(f"Final answer ({problem['units']})", placeholder=f"Example: {sci(problem['correct_answer'])} or {sci(problem['correct_answer'])} {problem['units']}")
            st.caption(f"Accepted format: a number with optional units, such as {sci(problem['correct_answer'])} or {sci(problem['correct_answer'])} {problem['units']}.")
        else:
            student_answer = st.text_input("Final answer")
        show_work = st.text_area("Show work (optional)")
        confidence = st.slider("Confidence", 1, 5, 3, help="1 = Guessing, 5 = Certain")
        submitted = st.form_submit_button("Check answer")
    if submitted:
        is_correct, note, warning = grade_answer(problem, student_answer)
        save_attempt(problem, mode, student_answer, show_work, is_correct, confidence)
        if is_correct:
            st.success("Correct.")
        else:
            st.error("Not quite.")
        st.write(note)
        if warning:
            st.warning(warning)
        st.write(f"Correct answer: **{problem['display_answer']}**")
        st.markdown("**Worked solution**")
        st.text(problem["worked_solution"])


def quiz_mode():
    st.header("Quiz Mode")
    subject, topics, difficulty = subject_topic_controls("quiz", multi_topic=True)
    count = st.number_input("Number of quiz problems", min_value=1, max_value=25, value=5)

    if st.button("Start new quiz", type="primary", disabled=not topics):
        st.session_state.quiz = [make_problem(subject, random.choice(topics), difficulty) for _ in range(int(count))]
        st.session_state.quiz_submitted = False

    quiz = st.session_state.get("quiz", [])
    if not quiz:
        st.info("Choose quiz settings and start a quiz.")
        return

    answers = []
    with st.form("quiz_form"):
        for i, problem in enumerate(quiz, start=1):
            st.markdown(f"**Problem {i}: {problem['topic']}**")
            st.write(problem["prompt"])
            label = "Final answer"
            if problem["answer_type"] == "numeric" and problem["units"]:
                label = f"Final answer ({problem['units']})"
            answers.append(
                {
                    "answer": st.text_input(label, key=f"quiz_answer_{i}"),
                    "work": st.text_area("Show work (optional)", key=f"quiz_work_{i}"),
                    "confidence": st.slider("Confidence", 1, 5, 3, key=f"quiz_confidence_{i}"),
                }
            )
            if problem["answer_type"] == "numeric" and problem["units"]:
                st.caption(f"Accepted format: a number with optional units, such as {sci(problem['correct_answer'])} or {sci(problem['correct_answer'])} {problem['units']}.")
        submitted = st.form_submit_button("Submit quiz")

    if submitted:
        correct_count = 0
        st.session_state.quiz_submitted = True
        st.subheader("Quiz Review")
        for i, (problem, answer) in enumerate(zip(quiz, answers), start=1):
            is_correct, note, warning = grade_answer(problem, answer["answer"])
            correct_count += int(is_correct)
            save_attempt(problem, "Quiz", answer["answer"], answer["work"], is_correct, answer["confidence"])
            st.markdown(f"**Problem {i}: {'Correct' if is_correct else 'Incorrect'}**")
            st.write(problem["prompt"])
            st.write(note)
            if warning:
                st.warning(warning)
            st.write(f"Correct answer: **{problem['display_answer']}**")
            st.text(problem["worked_solution"])
        st.success(f"Final score: {correct_count} / {len(quiz)} ({100 * correct_count / len(quiz):.1f}%)")


def dashboard():
    st.header("Dashboard")
    attempts = attempts_rows()
    summaries = summary_rows()

    if not attempts:
        st.info("No attempts yet. Complete a practice problem or quiz to populate the dashboard.")
        return

    total = len(attempts)
    correct = sum(row["is_correct"] for row in attempts)
    st.metric("Overall accuracy", f"{100 * correct / total:.1f}%", f"{correct}/{total} correct")

    left, right = st.columns(2)
    with left:
        st.subheader("Accuracy by Subject, Topic, and Difficulty")
        st.dataframe([dict(row) for row in summaries], use_container_width=True)
    with right:
        st.subheader("Most Missed Topics")
        missed = {}
        for row in attempts:
            if not row["is_correct"]:
                key = (row["subject"], row["topic"])
                missed[key] = missed.get(key, 0) + 1
        missed_rows = [{"subject": k[0], "topic": k[1], "misses": v} for k, v in sorted(missed.items(), key=lambda x: x[1], reverse=True)]
        st.dataframe(missed_rows, use_container_width=True)

    st.subheader("Recent Attempts")
    st.dataframe([dict(row) for row in attempts[:25]], use_container_width=True)

    low_conf = [dict(row) for row in attempts if row["confidence"] is not None and row["confidence"] <= 2]
    st.subheader("Low-Confidence Topics")
    st.dataframe(low_conf[:20], use_container_width=True)

    st.download_button("Export attempt history CSV", rows_to_csv(attempts), "attempt_history.csv", "text/csv")
    st.download_button("Export performance summary CSV", rows_to_csv(summaries), "performance_summary.csv", "text/csv")


def sample_problems():
    st.header("Sample Generated Problems")
    st.write("These are generated live and are useful for testing the app.")
    samples = [
        make_problem("Physics II", "Coulomb's Law", "Easy"),
        make_problem("Physics II", "Ohm's Law", "Easy"),
        make_problem("Intro Cryptography", "Modular arithmetic", "Easy"),
        make_problem("Intro Cryptography", "Toy RSA encryption/decryption", "Easy"),
    ]
    for problem in samples:
        st.markdown(f"**{problem['subject']} - {problem['topic']}**")
        st.write(problem["prompt"])
        st.write(f"Answer: {problem['display_answer']}")
        st.text(problem["worked_solution"])


if __name__ == "__main__":
    main()
