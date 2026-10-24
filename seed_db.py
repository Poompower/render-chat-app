import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "store.db")

def init_db(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        rating REAL NOT NULL,
        warranty_months INTEGER NOT NULL
    )
    """)

    cur.execute("""
    CREATE TABLE orders (
        order_id TEXT PRIMARY KEY,
        customer_name TEXT NOT NULL,
        customer_email TEXT NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        total_price REAL NOT NULL,
        status TEXT NOT NULL,
        order_date TEXT NOT NULL,
        tracking_number TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    cur.execute("""
    CREATE TABLE returns (
        return_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL,
        refund_amount REAL NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    )
    """)

    # Populate Products (Tech Gadgets & Peripherals)
    products = [
        ("PRD-101", "OmniTech AeroPulse ANC-X", "Audio", 4590.0, 42, 4.8, 12),
        ("PRD-102", "OmniTech ChronoFit Pro", "Wearables", 3290.0, 18, 4.6, 12),
        ("PRD-103", "OmniTech TitanBook 14", "Laptops", 38900.0, 9, 4.9, 12),
        ("PRD-104", "OmniTech MechWave RGB Keyboard", "Accessories", 2490.0, 65, 4.7, 12),
        ("PRD-105", "OmniTech SonicBuds Wireless", "Audio", 1890.0, 5, 4.3, 12),
        ("PRD-106", "OmniTech Clarity 4K Webcam", "Accessories", 2190.0, 24, 4.5, 12),
        ("PRD-107", "OmniTech PowerCore 100W GaN Charger", "Accessories", 1290.0, 80, 4.8, 12),
        ("PRD-108", "OmniTech VisionAir 4K Drone", "Drones", 18500.0, 4, 4.6, 12),
        ("PRD-109", "OmniTech ErgoGlide Wireless Mouse", "Accessories", 990.0, 110, 4.4, 12),
        ("PRD-110", "OmniTech ProTab 11 Tablet", "Tablets", 14900.0, 14, 4.5, 12),
        ("PRD-111", "OmniTech SoundBar Cinema 2.1", "Audio", 3790.0, 12, 4.2, 12),
        ("PRD-112", "OmniTech AeroPulse Replacement Ear Cushions", "Accessories", 490.0, 95, 4.7, 6),
        ("PRD-113", "OmniTech ChronoFit Sport Strap", "Wearables", 390.0, 72, 4.6, 6),
        ("PRD-114", "OmniTech USB-C Thunderbolt 4 Cable (2m)", "Accessories", 690.0, 140, 4.9, 12),
        ("PRD-115", "OmniTech Gaming Headset HyperBlast", "Audio", 2890.0, 21, 4.4, 12)
    ]

    cur.executemany("""
    INSERT INTO products (sku, name, category, price, stock, rating, warranty_months)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, products)

    # Populate Orders
    orders = [
        ("ORD-1001", "Somchai Prasert", "somchai@email.com", 1, 1, 4590.0, "delivered", "2026-10-01", "TH-KRY-882910"),
        ("ORD-1002", "Anongporn Wongsuwan", "anongporn@email.com", 2, 1, 3290.0, "delivered", "2026-10-05", "TH-EXP-772190"),
        ("ORD-1003", "Kittipong Chaiyaphum", "kittipong@email.com", 3, 1, 38900.0, "shipped", "2026-10-21", "TH-KRY-991201"),
        ("ORD-1004", "Natdanai Siriporn", "natdanai@email.com", 4, 2, 4980.0, "delivered", "2026-09-15", "TH-EXP-551234"),
        ("ORD-1005", "Pornthip Suksan", "pornthip@email.com", 5, 1, 1890.0, "delivered", "2026-10-10", "TH-KRY-441098"),
        ("ORD-1006", "Wichai Rattanakorn", "wichai@email.com", 1, 2, 9180.0, "delivered", "2026-10-12", "TH-KRY-331872"),
        ("ORD-1007", "Sasithorn Maneewan", "sasithorn@email.com", 8, 1, 18500.0, "processing", "2026-10-23", None),
        ("ORD-1008", "Chaiwat Boonsri", "chaiwat@email.com", 7, 3, 3870.0, "shipped", "2026-10-22", "TH-EXP-662911"),
        ("ORD-1009", "Benjamaporn Thani", "benjamaporn@email.com", 10, 1, 14900.0, "cancelled", "2026-10-18", None),
        ("ORD-1010", "Teerapat Kaewmanee", "teerapat@email.com", 2, 1, 3290.0, "delivered", "2026-09-28", "TH-EXP-119283"),
        ("ORD-1011", "Jirawat Narkvilai", "jirawat@email.com", 4, 1, 2490.0, "returned", "2026-10-02", "TH-KRY-661002"),
        ("ORD-1012", "Malee Sangkhum", "malee@email.com", 6, 1, 2190.0, "processing", "2026-10-24", None),
        ("ORD-1013", "Siriwan Chokdee", "siriwan@email.com", 9, 2, 1980.0, "delivered", "2026-10-14", "TH-EXP-889123"),
        ("ORD-1014", "Arthit Prasertsuk", "arthit@email.com", 1, 1, 4590.0, "processing", "2026-10-24", None),
        ("ORD-1015", "Kanchana Sriwichai", "kanchana@email.com", 3, 1, 38900.0, "delivered", "2026-09-10", "TH-KRY-551982"),
        ("ORD-1016", "Thanaporn Somboon", "thanaporn@email.com", 11, 1, 3790.0, "delivered", "2026-10-15", "TH-EXP-771992"),
        ("ORD-1017", "Rungroj Jaidee", "rungroj@email.com", 14, 4, 2760.0, "delivered", "2026-10-17", "TH-KRY-112877"),
        ("ORD-1018", "Supaporn Dee", "supaporn@email.com", 15, 1, 2890.0, "shipped", "2026-10-22", "TH-EXP-992812"),
        ("ORD-1019", "Narongchai Wattana", "narongchai@email.com", 2, 2, 6580.0, "delivered", "2026-10-08", "TH-KRY-334991"),
        ("ORD-1020", "Varanya Srisuk", "varanya@email.com", 4, 1, 2490.0, "delivered", "2026-10-19", "TH-EXP-441882")
    ]

    cur.executemany("""
    INSERT INTO orders (order_id, customer_name, customer_email, product_id, quantity, total_price, status, order_date, tracking_number)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, orders)

    # Populate Returns
    returns = [
        ("RET-501", "ORD-1011", "Ordered wrong switch type (wanted Brown, received Red)", "approved", 2490.0, "2026-10-06"),
        ("RET-502", "ORD-1004", "Keyboard keycap scratched upon unboxing", "refunded", 2490.0, "2026-09-20"),
        ("RET-503", "ORD-1002", "Wristband size too large for small wrist", "rejected", 0.0, "2026-10-16"),
        ("RET-504", "ORD-1010", "Battery draining faster than expected", "approved", 3290.0, "2026-10-04"),
        ("RET-505", "ORD-1015", "Screen flickering issue after 3 weeks", "approved", 38900.0, "2026-10-01")
    ]

    cur.executemany("""
    INSERT INTO returns (return_id, order_id, reason, status, refund_amount, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, returns)

    conn.commit()
    conn.close()
    print(f"Database successfully seeded at {db_path} with {len(products)} products, {len(orders)} orders, and {len(returns)} returns.")

if __name__ == "__main__":
    init_db()
