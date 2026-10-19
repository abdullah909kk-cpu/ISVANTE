import sqlite3
import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """)

    # Admins table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Categories / Collections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT,
        image_url TEXT,
        display_order INTEGER DEFAULT 0
    )
    """)

    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        sku TEXT UNIQUE NOT NULL,
        category_id INTEGER,
        price REAL NOT NULL,
        compare_at_price REAL,
        is_featured INTEGER DEFAULT 0,
        is_bestseller INTEGER DEFAULT 0,
        is_new_arrival INTEGER DEFAULT 0,
        stock INTEGER DEFAULT 15,
        short_description TEXT,
        description TEXT,
        movement TEXT,
        case_material TEXT,
        strap_material TEXT,
        dial_size TEXT,
        water_resistance TEXT,
        glass_material TEXT,
        warranty TEXT,
        color TEXT,
        main_image TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
    )
    """)

    # Product Gallery Images
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        image_url TEXT NOT NULL,
        display_order INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    )
    """)

    # Coupons
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        discount_type TEXT NOT NULL, -- 'percentage' or 'fixed'
        discount_value REAL NOT NULL,
        min_order_value REAL DEFAULT 0,
        max_uses INTEGER DEFAULT 1000,
        uses_count INTEGER DEFAULT 0,
        expires_at DATETIME,
        is_active INTEGER DEFAULT 1
    )
    """)

    # Orders
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_email TEXT,
        customer_phone TEXT NOT NULL,
        customer_whatsapp TEXT,
        address TEXT NOT NULL,
        city TEXT NOT NULL,
        province TEXT NOT NULL,
        postal_code TEXT,
        notes TEXT,
        payment_method TEXT NOT NULL, -- 'cod' or 'online'
        payment_status TEXT DEFAULT 'pending', -- 'pending', 'paid', 'failed'
        order_status TEXT DEFAULT 'Pending', -- 'Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled'
        courier_name TEXT,
        tracking_number TEXT,
        subtotal REAL NOT NULL,
        shipping_fee REAL NOT NULL,
        discount_amount REAL DEFAULT 0,
        coupon_code TEXT,
        total REAL NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Order Items
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        total REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE SET NULL
    )
    """)

    # Customer Reviews
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        customer_name TEXT NOT NULL,
        city TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
        review_text TEXT NOT NULL,
        is_verified INTEGER DEFAULT 1,
        is_approved INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
    )
    """)

    conn.commit()

    # Seed Default Settings if empty
    settings_seed = {
        "store_name": "ISVANTE",
        "tagline": "CRAFTED TO STAND OUT",
        "logo_url": "/static/images/isvante_logo_circle.png",
        "whatsapp_number": Config.DEFAULT_WHATSAPP_NUMBER,
        "contact_phone": Config.DEFAULT_CONTACT_PHONE,
        "contact_email": Config.DEFAULT_CONTACT_EMAIL,
        "shipping_fee": str(Config.DEFAULT_SHIPPING_FEE),
        "free_shipping_threshold": str(Config.DEFAULT_FREE_SHIPPING_THRESHOLD),
        "cod_enabled": "1",
        "announcement_text": "Cash on Delivery Available Across Pakistan | Free Nationwide Shipping on Orders Above Rs. 5,000",
        "instagram_url": "https://instagram.com/isvante.pk",
        "facebook_url": "https://facebook.com/isvante.pk",
        "tiktok_url": "https://tiktok.com/@isvante.pk",
        "courier_partners": "Trax Logistics, TCS Express, Leopard Courier, CallCourier, PostEx",
        "store_address": "ISVANTE Horology Studio, Gulberg III, Lahore, Pakistan"
    }

    for k, v in settings_seed.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Seed Admin User if none exists
    cursor.execute("SELECT COUNT(*) as cnt FROM admins")
    if cursor.fetchone()["cnt"] == 0:
        hashed = generate_password_hash("isvantepakistan")
        cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", ("admin", hashed))

    # Seed Categories / Collections
    collections = [
        ("Classic", "classic", "Timeless dress watches designed for formal elegance and refined character.", "/static/images/heritage_classic.jpg", 1),
        ("Luxury", "luxury", "Exquisite prestige timepieces built with top-tier finishing and open-heart automatic movements.", "/static/images/royal_eclipse.jpg", 2),
        ("Minimal", "minimal", "Contemporary Scandinavian simplicity paired with ultra-slim cases for modern daily wear.", "/static/images/aurelia_minimal.jpg", 3),
        ("Chronograph", "chronograph", "Precision split-second timekeeping powered by high-grade Japanese movements.", "/static/images/chrono_sovereign.jpg", 4),
        ("Everyday", "everyday", "Rugged sophistication and versatile water-resistant builds engineered for daily luxury.", "/static/images/nautique_diver.jpg", 5),
        ("New Arrivals", "new-arrivals", "The latest horological releases featuring celestial moonphases and limited dials.", "/static/images/celestia_moonphase.jpg", 6)
    ]
    for name, slug, desc, img, order in collections:
        cursor.execute("INSERT OR IGNORE INTO categories (name, slug, description, image_url, display_order) VALUES (?, ?, ?, ?, ?)",
                       (name, slug, desc, img, order))

    conn.commit()

    # Seed Products if table empty
    cursor.execute("SELECT COUNT(*) as cnt FROM products")
    if cursor.fetchone()["cnt"] == 0:
        # Category ID lookup
        cursor.execute("SELECT id, slug FROM categories")
        cat_map = {row["slug"]: row["id"] for row in cursor.fetchall()}

        products = [
            {
                "name": "ISVANTE Chrono Sovereign",
                "slug": "isvante-chrono-sovereign",
                "sku": "ISV-CS-01",
                "category_id": cat_map.get("chronograph"),
                "price": 24500.0,
                "compare_at_price": 29500.0,
                "is_featured": 1,
                "is_bestseller": 1,
                "is_new_arrival": 1,
                "stock": 18,
                "short_description": "Prestige chronograph with an emerald sunburst dial, gold tachymeter bezel, and solid 316L gold link bracelet.",
                "description": "Crafted to stand out, the ISVANTE Chrono Sovereign commands presence. Featuring a striking deep emerald green sunray dial housed in a mirror-polished 316L stainless steel case finished in champagne gold PVD. The triple sub-dial layout offers 1/10th second chronograph precision, while the anti-reflective sapphire crystal ensures crystal-clear readability under any light. Fitted with a solid link butterfly clasp bracelet.",
                "movement": "Japanese Seiko VK63 Mecha-Quartz Chronograph",
                "case_material": "316L Surgical Stainless Steel (Champagne Gold PVD)",
                "strap_material": "Solid Link 316L Stainless Steel Bracelet with Butterfly Clasp",
                "dial_size": "41mm Diameter | 11.5mm Thickness",
                "water_resistance": "10 ATM / 100 Meters (Screw-down Crown)",
                "glass_material": "Scratch-Resistant Sapphire Crystal with AR Coating",
                "warranty": "1 Year Official ISVANTE Nationwide Warranty",
                "color": "Emerald Green & Champagne Gold",
                "main_image": "/static/images/chrono_sovereign.jpg",
                "gallery": ["/static/images/chrono_sovereign.jpg", "/static/images/hero_banner.jpg"]
            },
            {
                "name": "ISVANTE Royal Eclipse",
                "slug": "isvante-royal-eclipse",
                "sku": "ISV-RE-02",
                "category_id": cat_map.get("luxury"),
                "price": 28900.0,
                "compare_at_price": 34000.0,
                "is_featured": 1,
                "is_bestseller": 1,
                "is_new_arrival": 0,
                "stock": 12,
                "short_description": "Ultra-sleek obsidian black minimalist dial paired with a warm champagne gold case and genuine Italian leather.",
                "description": "The Royal Eclipse embodies understated luxury. The deep matte obsidian dial features hand-applied gold baton indices and diamond-cut dauphine hands. Paired with a hand-stitched black genuine alligator-grain Italian leather strap, this timepiece transitions effortlessly from high-stakes boardroom meetings to black-tie evening galas in Lahore, Karachi, and Islamabad.",
                "movement": "Miyota 9015 Automatic Mechanical / Premium High-Beat Movement",
                "case_material": "316L Stainless Steel with 18K Gold Electroplating",
                "strap_material": "Handcrafted Genuine Italian Calfskin Leather",
                "dial_size": "40mm Diameter | 9.8mm Ultra-Slim Profile",
                "water_resistance": "5 ATM / 50 Meters",
                "glass_material": "Double-Domed Sapphire Crystal with Anti-Glare Coating",
                "warranty": "1 Year Official ISVANTE Nationwide Warranty",
                "color": "Obsidian Black & Champagne Gold",
                "main_image": "/static/images/royal_eclipse.jpg",
                "gallery": ["/static/images/royal_eclipse.jpg", "/static/images/hero_banner.jpg"]
            },
            {
                "name": "ISVANTE Heritage Classic",
                "slug": "isvante-heritage-classic",
                "sku": "ISV-HC-03",
                "category_id": cat_map.get("classic"),
                "price": 19500.0,
                "compare_at_price": 23000.0,
                "is_featured": 1,
                "is_bestseller": 1,
                "is_new_arrival": 0,
                "stock": 25,
                "short_description": "Pure porcelain white dial, traditional Roman numerals, flame-blued hands, and rich cognac leather strap.",
                "description": "An homage to timeless Swiss horology. The ISVANTE Heritage Classic features an enamel-finish porcelain white dial framed by slender Roman numerals and striking thermal-blued hands. A subtle date aperture at 3 o'clock provides daily utility, while the textured cognac saddle leather strap offers unmatched wrist comfort for Pakistani climates.",
                "movement": "Precision Swiss-Engineered Quartz Movement",
                "case_material": "Polished 316L Stainless Steel with Rose Gold Accents",
                "strap_material": "Full-Grain Cognac Saddle Leather with Quick-Release Spring Bars",
                "dial_size": "39mm Diameter | 8.5mm Slim Profile",
                "water_resistance": "5 ATM / 50 Meters",
                "glass_material": "Sapphire Crystal Glass",
                "warranty": "1 Year Official ISVANTE Nationwide Warranty",
                "color": "Porcelain White & Cognac Tan",
                "main_image": "/static/images/heritage_classic.jpg",
                "gallery": ["/static/images/heritage_classic.jpg", "/static/images/hero_banner.jpg"]
            },
            {
                "name": "ISVANTE Aurelia Minimalist",
                "slug": "isvante-aurelia-minimalist",
                "sku": "ISV-AM-04",
                "category_id": cat_map.get("minimal"),
                "price": 16900.0,
                "compare_at_price": 19900.0,
                "is_featured": 1,
                "is_bestseller": 0,
                "is_new_arrival": 1,
                "stock": 30,
                "short_description": "Contemporary ultra-slim 7mm profile with a sunray champagne dial and supple Milanese mesh bracelet.",
                "description": "Simplicity elevated to fine art. The Aurelia Minimalist features an ultra-thin 7mm profile that glides effortlessly under any shirt cuff. The brushed gold sunburst dial interacts dynamically with natural light, paired with an infinitely adjustable magnetic Milanese mesh band that ensures a tailored fit on any wrist.",
                "movement": "Ultra-Thin Japanese Miyota GL20 Movement",
                "case_material": "316L Stainless Steel (Brushed Satin Gold)",
                "strap_material": "Interwoven 316L Stainless Steel Milanese Mesh Strap",
                "dial_size": "38mm Diameter | 7.0mm Ultra-Thin",
                "water_resistance": "3 ATM / 30 Meters (Splash Resistant)",
                "glass_material": "Hardened Mineral Crystal with Sapphire Hard-Coating",
                "warranty": "1 Year Official ISVANTE Nationwide Warranty",
                "color": "Brushed Champagne Gold",
                "main_image": "/static/images/aurelia_minimal.jpg",
                "gallery": ["/static/images/aurelia_minimal.jpg", "/static/images/hero_banner.jpg"]
            },
            {
                "name": "ISVANTE Celestia Moonphase",
                "slug": "isvante-celestia-moonphase",
                "sku": "ISV-CM-05",
                "category_id": cat_map.get("new-arrivals"),
                "price": 32500.0,
                "compare_at_price": 38000.0,
                "is_featured": 1,
                "is_bestseller": 0,
                "is_new_arrival": 1,
                "stock": 8,
                "short_description": "Stunning midnight aventurine dial with a functional gold moonphase complication and midnight blue alligator leather.",
                "description": "Inspired by the celestial heavens, the Celestia Moonphase features an aventurine dial that sparkles like a clear night sky over Hunza Valley. A complication window at 6 o'clock tracks the 29.5-day lunar cycle with a gleaming golden moon and stars. Hand-finished with an exhibition caseback and genuine midnight blue leather.",
                "movement": "Custom Automatic Moonphase Mechanical Movement (42-hr Power Reserve)",
                "case_material": "Mirror-Polished 316L Stainless Steel with 18K Yellow Gold Bezel",
                "strap_material": "Genuine Midnight Blue Alligator-Embossed Leather",
                "dial_size": "41mm Diameter | 12.2mm Profile",
                "water_resistance": "5 ATM / 50 Meters",
                "glass_material": "Scratch-Resistant Sapphire Crystal (Front & Exhibition Caseback)",
                "warranty": "1 Year Official ISVANTE Nationwide Warranty",
                "color": "Celestial Midnight Blue & Gold",
                "main_image": "/static/images/celestia_moonphase.jpg",
                "gallery": ["/static/images/celestia_moonphase.jpg", "/static/images/hero_banner.jpg"]
            },
            {
                "name": "ISVANTE Nautique Diver",
                "slug": "isvante-nautique-diver",
                "sku": "ISV-ND-06",
                "category_id": cat_map.get("everyday"),
                "price": 26900.0,
                "compare_at_price": 31000.0,
                "is_featured": 1,
                "is_bestseller": 1,
                "is_new_arrival": 0,
                "stock": 14,
                "short_description": "200m aquatic endurance with a unidirectional ceramic bezel, deep ocean blue dial, and solid oyster link bracelet.",
                "description": "Engineered for both sea and land. The Nautique Diver combines rugged durability with immaculate luxury finishing. Featuring a unidirectional rotating black ceramic bezel with engraved graduations, a deep ocean wave-texture dial, and Swiss Super-LumiNova BGW9 on indices and hands for exceptional glow in darkness. Water-resistant up to 200 meters.",
                "movement": "Seiko NH35A Automatic Mechanical (Hacking & Hand-Winding)",
                "case_material": "316L Solid Surgical Stainless Steel with Brushed Lugs",
                "strap_material": "Solid Oyster 316L Bracelet with Milled Divers Extension Clasp",
                "dial_size": "42mm Diameter | 13.0mm Thickness",
                "water_resistance": "20 ATM / 200 Meters with Screw-Down Crown & Caseback",
                "glass_material": "Flat Sapphire Crystal with Inner Cyclops Date Magnifier",
                "warranty": "1 Year Official ISVANTE Nationwide Warranty",
                "color": "Ocean Blue & Polished Steel",
                "main_image": "/static/images/nautique_diver.jpg",
                "gallery": ["/static/images/nautique_diver.jpg", "/static/images/hero_banner.jpg"]
            }
        ]

        for p in products:
            cursor.execute("""
            INSERT INTO products (
                name, slug, sku, category_id, price, compare_at_price,
                is_featured, is_bestseller, is_new_arrival, stock,
                short_description, description, movement, case_material,
                strap_material, dial_size, water_resistance, glass_material,
                warranty, color, main_image
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p["name"], p["slug"], p["sku"], p["category_id"], p["price"], p["compare_at_price"],
                p["is_featured"], p["is_bestseller"], p["is_new_arrival"], p["stock"],
                p["short_description"], p["description"], p["movement"], p["case_material"],
                p["strap_material"], p["dial_size"], p["water_resistance"], p["glass_material"],
                p["warranty"], p["color"], p["main_image"]
            ))
            prod_id = cursor.lastrowid
            for order_idx, img_url in enumerate(p["gallery"]):
                cursor.execute("INSERT INTO product_images (product_id, image_url, display_order) VALUES (?, ?, ?)",
                               (prod_id, img_url, order_idx))

        conn.commit()

    # Seed Coupons if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM coupons")
    if cursor.fetchone()["cnt"] == 0:
        cursor.execute("""
        INSERT INTO coupons (code, discount_type, discount_value, min_order_value, max_uses, uses_count, is_active)
        VALUES ('ISVANTE10', 'percentage', 10, 5000, 500, 12, 1)
        """)
        cursor.execute("""
        INSERT INTO coupons (code, discount_type, discount_value, min_order_value, max_uses, uses_count, is_active)
        VALUES ('WELCOME1500', 'fixed', 1500, 15000, 300, 7, 1)
        """)
        conn.commit()

    # Seed Authentic Pakistani Customer Reviews if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM reviews")
    if cursor.fetchone()["cnt"] == 0:
        reviews_data = [
            (1, "Hamza Tariq", "Lahore, DHA Phase 5", 5, "I was hesitant to order a watch online in Pakistan, but ISVANTE exceeded all expectations. Ordered via Cash on Delivery, received it in 2 days via Trax. The packaging was royal - black velvet box, warranty card, and the Chrono Sovereign feels heavy and genuine. MashAllah, absolute world-class quality!", 1),
            (1, "Bilal Ahmed", "Karachi, Clifton", 5, "The finishing on the bezel and dial is comparable to imported Swiss watches costing 4x more. The WhatsApp concierge confirmed my ring size and order details within 10 minutes. 100% recommended for Pakistani watch enthusiasts.", 1),
            (2, "Dr. Salman Qureshi", "Islamabad, F-7/2", 5, "The Royal Eclipse is minimalism at its finest. The leather is supple Italian grade and doesn't sweat in our warm weather. Wearing it daily to the clinic and receiving compliments continuously.", 1),
            (3, "Saad Farooq", "Faisalabad, Kohinoor City", 5, "Ordered the Heritage Classic as an anniversary gift. Elegant Roman dial, sapphire glass is genuine (did the water droplet test). Cash on delivery delivery was hassle-free with TCS.", 1),
            (4, "Daniyal Malik", "Rawalpindi, Bahria Town", 5, "Aurelia Minimalist is breathtaking in person. Photos don't do justice to the champagne sunburst effect under sunlight. The Milanese mesh feels silky smooth.", 1),
            (6, "Zubair Khan", "Peshawar, University Town", 5, "The Nautique Diver has serious wrist presence. The ceramic bezel clicks cleanly with 120 clicks, no backplay. Truly Pakistani luxury done right.", 1)
        ]
        for pid, name, city, rating, text, verified in reviews_data:
            cursor.execute("""
            INSERT INTO reviews (product_id, customer_name, city, rating, review_text, is_verified, is_approved)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (pid, name, city, rating, text, verified))
        conn.commit()

    conn.close()

# Public Data Access Layer
def get_settings():
    conn = get_db()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}

def update_setting(key, value):
    conn = get_db()
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
    conn.commit()
    conn.close()

def get_all_categories():
    conn = get_db()
    cats = conn.execute("SELECT * FROM categories ORDER BY display_order ASC").fetchall()
    conn.close()
    return [dict(cat) for cat in cats]

def get_products(category_slug=None, search=None, sort_by=None, min_price=None, max_price=None, limit=None, offset=0, featured_only=False, bestseller_only=False, new_arrivals_only=False):
    conn = get_db()
    query = """
    SELECT p.*, c.name as category_name, c.slug as category_slug,
           (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id AND r.is_approved = 1) as review_count,
           (SELECT COALESCE(AVG(rating), 5.0) FROM reviews r WHERE r.product_id = p.id AND r.is_approved = 1) as avg_rating
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE 1=1
    """
    params = []

    if category_slug:
        query += " AND c.slug = ?"
        params.append(category_slug)

    if search:
        query += " AND (p.name LIKE ? OR p.short_description LIKE ? OR p.sku LIKE ? OR p.movement LIKE ?)"
        s_term = f"%{search}%"
        params.extend([s_term, s_term, s_term, s_term])

    if min_price is not None:
        query += " AND p.price >= ?"
        params.append(min_price)

    if max_price is not None:
        query += " AND p.price <= ?"
        params.append(max_price)

    if featured_only:
        query += " AND p.is_featured = 1"

    if bestseller_only:
        query += " AND p.is_bestseller = 1"

    if new_arrivals_only:
        query += " AND p.is_new_arrival = 1"

    # Sorting
    if sort_by == "price_asc":
        query += " ORDER BY p.price ASC"
    elif sort_by == "price_desc":
        query += " ORDER BY p.price DESC"
    elif sort_by == "newest":
        query += " ORDER BY p.created_at DESC"
    elif sort_by == "popularity":
        query += " ORDER BY p.is_bestseller DESC, p.is_featured DESC, avg_rating DESC"
    else:
        query += " ORDER BY p.id ASC"

    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_product_by_slug(slug):
    conn = get_db()
    row = conn.execute("""
    SELECT p.*, c.name as category_name, c.slug as category_slug,
           (SELECT COUNT(*) FROM reviews r WHERE r.product_id = p.id AND r.is_approved = 1) as review_count,
           (SELECT COALESCE(AVG(rating), 5.0) FROM reviews r WHERE r.product_id = p.id AND r.is_approved = 1) as avg_rating
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE p.slug = ?
    """, (slug,)).fetchone()

    if not row:
        conn.close()
        return None

    prod = dict(row)
    images = conn.execute("SELECT image_url FROM product_images WHERE product_id = ? ORDER BY display_order ASC", (prod["id"],)).fetchall()
    prod["gallery"] = [img["image_url"] for img in images] or [prod["main_image"]]
    
    # Reviews
    revs = conn.execute("SELECT * FROM reviews WHERE product_id = ? AND is_approved = 1 ORDER BY created_at DESC", (prod["id"],)).fetchall()
    prod["reviews"] = [dict(r) for r in revs]

    conn.close()
    return prod

def get_product_by_id(product_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_related_products(product_id, category_id, limit=4):
    conn = get_db()
    rows = conn.execute("""
    SELECT p.*, c.name as category_name
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE p.id != ? AND (p.category_id = ? OR p.is_featured = 1)
    ORDER BY RANDOM() LIMIT ?
    """, (product_id, category_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def validate_coupon(code, subtotal):
    conn = get_db()
    row = conn.execute("SELECT * FROM coupons WHERE UPPER(code) = UPPER(?) AND is_active = 1", (code.strip(),)).fetchone()
    conn.close()

    if not row:
        return {"valid": False, "message": "Invalid discount coupon code."}

    coupon = dict(row)
    if coupon["min_order_value"] and subtotal < coupon["min_order_value"]:
        return {"valid": False, "message": f"This coupon requires a minimum order of Rs. {int(coupon['min_order_value']):,}."}

    if coupon["max_uses"] and coupon["uses_count"] >= coupon["max_uses"]:
        return {"valid": False, "message": "This coupon has reached its maximum usage limit."}

    if coupon["discount_type"] == "percentage":
        discount = (subtotal * coupon["discount_value"]) / 100.0
    else:
        discount = float(coupon["discount_value"])

    discount = min(discount, subtotal)
    return {
        "valid": True,
        "code": coupon["code"],
        "discount_type": coupon["discount_type"],
        "discount_value": coupon["discount_value"],
        "discount_amount": discount,
        "message": f"Coupon applied successfully! You saved Rs. {int(discount):,}."
    }

def create_order(order_data):
    """
    Creates a real order in the database with customer info, items, pricing,
    and returns the unique order number and order object.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Generate unique luxurious order number e.g. ISV-83921
    import random
    random_digits = random.randint(10000, 99999)
    order_number = f"ISV-{random_digits}"

    # Calculate item totals safely from database prices
    items = order_data.get("items", [])
    if not items:
        conn.close()
        raise ValueError("Cart is empty.")

    subtotal = 0.0
    verified_items = []

    for item in items:
        pid = item.get("id") or item.get("product_id")
        qty = int(item.get("quantity", 1))
        prod = cursor.execute("SELECT id, name, price, stock FROM products WHERE id = ?", (pid,)).fetchone()
        if not prod:
            continue
        line_total = prod["price"] * qty
        subtotal += line_total
        verified_items.append({
            "product_id": prod["id"],
            "product_name": prod["name"],
            "price": prod["price"],
            "quantity": qty,
            "total": line_total
        })

    # Calculate shipping
    settings = get_settings()
    shipping_threshold = float(settings.get("free_shipping_threshold", Config.DEFAULT_FREE_SHIPPING_THRESHOLD))
    standard_shipping = float(settings.get("shipping_fee", Config.DEFAULT_SHIPPING_FEE))

    shipping_fee = 0.0 if subtotal >= shipping_threshold else standard_shipping

    # Apply Coupon
    discount_amount = 0.0
    coupon_code = order_data.get("coupon_code", "").strip()
    if coupon_code:
        coupon_res = validate_coupon(coupon_code, subtotal)
        if coupon_res["valid"]:
            discount_amount = coupon_res["discount_amount"]
            cursor.execute("UPDATE coupons SET uses_count = uses_count + 1 WHERE UPPER(code) = UPPER(?)", (coupon_code,))

    total = max(0.0, (subtotal - discount_amount) + shipping_fee)

    payment_method = order_data.get("payment_method", "cod").lower()
    payment_status = "paid" if payment_method == "online" and order_data.get("payment_gateway_ref") else "pending"

    cursor.execute("""
    INSERT INTO orders (
        order_number, customer_name, customer_email, customer_phone, customer_whatsapp,
        address, city, province, postal_code, notes, payment_method, payment_status,
        order_status, courier_name, tracking_number, subtotal, shipping_fee, discount_amount,
        coupon_code, total, created_at, updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending', 'Trax Logistics', NULL, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (
        order_number,
        order_data.get("customer_name"),
        order_data.get("customer_email"),
        order_data.get("customer_phone"),
        order_data.get("customer_whatsapp") or order_data.get("customer_phone"),
        order_data.get("address"),
        order_data.get("city"),
        order_data.get("province"),
        order_data.get("postal_code"),
        order_data.get("notes"),
        payment_method,
        payment_status,
        subtotal,
        shipping_fee,
        discount_amount,
        coupon_code if discount_amount > 0 else None,
        total
    ))

    order_id = cursor.lastrowid

    # Insert order items and deduct inventory
    for v_item in verified_items:
        cursor.execute("""
        INSERT INTO order_items (order_id, product_id, product_name, price, quantity, total)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, v_item["product_id"], v_item["product_name"], v_item["price"], v_item["quantity"], v_item["total"]))
        
        # Decrement stock safely
        cursor.execute("UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?", (v_item["quantity"], v_item["product_id"]))

    conn.commit()
    conn.close()

    return {
        "order_id": order_id,
        "order_number": order_number,
        "total": total,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "discount_amount": discount_amount,
        "payment_method": payment_method,
        "payment_status": payment_status,
        "customer_name": order_data.get("customer_name"),
        "customer_phone": order_data.get("customer_phone"),
        "customer_whatsapp": order_data.get("customer_whatsapp") or order_data.get("customer_phone"),
        "items": verified_items
    }

def get_order_by_number(order_number):
    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number.strip().upper(),)).fetchone()
    if not row:
        conn.close()
        return None

    order = dict(row)
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
    order["items"] = [dict(it) for it in items]
    conn.close()
    return order

def track_order(order_number, phone_number):
    conn = get_db()
    clean_num = order_number.strip().upper()
    # allow flexible phone matching (last 7 digits or exact)
    clean_phone = phone_number.replace(" ", "").replace("-", "").replace("+", "")[-7:]

    row = conn.execute("""
    SELECT * FROM orders 
    WHERE order_number = ? AND (
        REPLACE(REPLACE(REPLACE(customer_phone, ' ', ''), '-', ''), '+', '') LIKE ?
        OR REPLACE(REPLACE(REPLACE(customer_whatsapp, ' ', ''), '-', ''), '+', '') LIKE ?
    )
    """, (clean_num, f"%{clean_phone}", f"%{clean_phone}")).fetchone()

    if not row:
        conn.close()
        return None

    order = dict(row)
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()
    order["items"] = [dict(it) for it in items]
    conn.close()
    return order

def add_review(product_id, customer_name, city, rating, review_text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO reviews (product_id, customer_name, city, rating, review_text, is_verified, is_approved)
    VALUES (?, ?, ?, ?, ?, 1, 1)
    """, (product_id, customer_name.strip(), city.strip(), int(rating), review_text.strip()))
    conn.commit()
    rev_id = cursor.lastrowid
    conn.close()
    return rev_id
