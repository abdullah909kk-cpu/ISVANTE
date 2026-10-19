import os
import json
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory, abort
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
import database
import ai_concierge

app = Flask(__name__)
app.config.from_object(Config)

# Ensure static upload directory exists
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize DB on start
with app.app_context():
    database.init_db()

# Context processor for templates to always have brand settings & logo
@app.context_processor
def inject_global_data():
    settings = database.get_settings()
    categories = database.get_all_categories()
    return {
        "settings": settings,
        "categories": categories,
        "is_admin_logged_in": "admin_user" in session
    }

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_user" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "Unauthorized"}), 401
            return redirect(url_for("admin_login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# PUBLIC HTML ROUTES
# ==========================================

@app.route("/")
def index_page():
    featured = database.get_products(featured_only=True, limit=6)
    bestsellers = database.get_products(bestseller_only=True, limit=4)
    new_arrivals = database.get_products(new_arrivals_only=True, limit=4)
    categories = database.get_all_categories()
    
    # Recent authentic customer reviews
    conn = database.get_db()
    reviews = conn.execute("""
        SELECT r.*, p.name as product_name, p.main_image as product_image
        FROM reviews r
        LEFT JOIN products p ON r.product_id = p.id
        WHERE r.is_approved = 1
        ORDER BY r.created_at DESC LIMIT 6
    """).fetchall()
    conn.close()

    return render_template(
        "index.html",
        featured=featured,
        bestsellers=bestsellers,
        new_arrivals=new_arrivals,
        collections=categories,
        reviews=[dict(r) for r in reviews]
    )

@app.route("/shop")
def shop_page():
    category_slug = request.args.get("category") or request.args.get("collection")
    search = request.args.get("q")
    sort_by = request.args.get("sort", "popularity")
    
    min_p = request.args.get("min_price", type=float)
    max_p = request.args.get("max_price", type=float)
    
    products = database.get_products(
        category_slug=category_slug,
        search=search,
        sort_by=sort_by,
        min_price=min_p,
        max_price=max_p
    )
    categories = database.get_all_categories()

    return render_template(
        "shop.html",
        products=products,
        categories=categories,
        current_category=category_slug,
        current_search=search or "",
        current_sort=sort_by,
        min_p=min_p,
        max_p=max_p
    )

@app.route("/collection/<slug>")
def collection_page(slug):
    return redirect(url_for("shop_page", collection=slug))

@app.route("/product/<slug>")
def product_page(slug):
    product = database.get_product_by_slug(slug)
    if not product:
        abort(404)
    
    related = database.get_related_products(product["id"], product["category_id"], limit=4)
    settings = database.get_settings()
    
    # Pre-generate WhatsApp direct link
    wa_num = settings.get("whatsapp_number", Config.DEFAULT_WHATSAPP_NUMBER).replace("+", "").replace(" ", "")
    wa_message = f"Hello ISVANTE, I am interested in the {product['name']} (Price: Rs. {int(product['price']):,}). Is it available for Cash on Delivery?"
    import urllib.parse
    wa_link = f"https://wa.me/{wa_num}?text={urllib.parse.quote(wa_message)}"

    return render_template(
        "product.html",
        product=product,
        related=related,
        whatsapp_product_link=wa_link
    )

@app.route("/cart")
def cart_page():
    return render_template("cart.html")

@app.route("/checkout")
def checkout_page():
    return render_template("checkout.html")

@app.route("/order-confirmation/<order_number>")
def order_confirmation_page(order_number):
    order = database.get_order_by_number(order_number)
    if not order:
        abort(404)

    settings = database.get_settings()
    wa_num = settings.get("whatsapp_number", Config.DEFAULT_WHATSAPP_NUMBER).replace("+", "").replace(" ", "")
    wa_text = f"Hello ISVANTE, I have placed order #{order['order_number']} for Rs. {int(order['total']):,} via {order['payment_method'].upper()}. Please confirm my shipment."
    import urllib.parse
    wa_confirm_link = f"https://wa.me/{wa_num}?text={urllib.parse.quote(wa_text)}"

    return render_template(
        "order_confirmation.html",
        order=order,
        whatsapp_confirm_link=wa_confirm_link
    )

@app.route("/track")
def track_page():
    return render_template("track.html")

@app.route("/about")
def about_page():
    return render_template("about.html")

@app.route("/contact")
def contact_page():
    return render_template("contact.html")

@app.route("/policies/<policy_name>")
def policy_page(policy_name):
    valid_policies = ["shipping", "returns", "privacy", "terms", "faqs"]
    if policy_name not in valid_policies:
        abort(404)
    return render_template("policy.html", active_policy=policy_name)

# ==========================================
# ADMIN HTML ROUTES
# ==========================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login_page():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        conn = database.get_db()
        admin = conn.execute("SELECT * FROM admins WHERE username = ?", (username,)).fetchone()
        conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_user"] = admin["username"]
            next_url = request.args.get("next") or url_for("admin_dashboard_page")
            return redirect(next_url)
        else:
            return render_template("admin_login.html", error="Invalid admin username or password.")

    if "admin_user" in session:
        return redirect(url_for("admin_dashboard_page"))
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_user", None)
    return redirect(url_for("admin_login_page"))

@app.route("/admin")
@admin_required
def admin_dashboard_page():
    return render_template("admin.html")

# ==========================================
# PUBLIC REST APIS
# ==========================================

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    return jsonify({"success": True, "settings": database.get_settings()})

@app.route("/api/products", methods=["GET"])
def api_get_products():
    category = request.args.get("category")
    search = request.args.get("q")
    sort = request.args.get("sort", "popularity")
    min_p = request.args.get("min_price", type=float)
    max_p = request.args.get("max_price", type=float)
    
    products = database.get_products(
        category_slug=category,
        search=search,
        sort_by=sort,
        min_price=min_p,
        max_price=max_p
    )
    return jsonify({"success": True, "count": len(products), "products": products})

@app.route("/api/products/<slug_or_id>", methods=["GET"])
def api_get_product_detail(slug_or_id):
    if slug_or_id.isdigit():
        prod = database.get_product_by_id(int(slug_or_id))
    else:
        prod = database.get_product_by_slug(slug_or_id)
        
    if not prod:
        return jsonify({"success": False, "error": "Product not found"}), 404
    return jsonify({"success": True, "product": prod})

@app.route("/api/categories", methods=["GET"])
def api_get_categories():
    return jsonify({"success": True, "categories": database.get_all_categories()})

@app.route("/api/coupons/validate", methods=["POST"])
def api_validate_coupon():
    data = request.get_json() or {}
    code = data.get("code", "")
    subtotal = float(data.get("subtotal", 0.0))
    result = database.validate_coupon(code, subtotal)
    return jsonify(result)

@app.route("/api/orders", methods=["POST"])
def api_place_order():
    data = request.get_json() or {}
    
    # Server-side validation
    required_fields = ["customer_name", "customer_phone", "address", "city", "province", "items"]
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({"success": False, "error": f"Missing required fields: {', '.join(missing)}"}), 400

    if not data.get("items") or len(data.get("items")) == 0:
        return jsonify({"success": False, "error": "Your shopping cart is empty."}), 400

    try:
        order_res = database.create_order(data)
        return jsonify({"success": True, "order": order_res}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/orders/track", methods=["GET"])
def api_track_order():
    order_num = request.args.get("order_number", "")
    phone = request.args.get("phone", "")

    if not order_num or not phone:
        return jsonify({"success": False, "error": "Please provide both Order Number and Phone Number."}), 400

    order = database.track_order(order_num, phone)
    if not order:
        return jsonify({"success": False, "error": "No order found matching those credentials. Please check your Order ID and phone number."}), 404

    return jsonify({"success": True, "order": order})

@app.route("/api/reviews", methods=["POST"])
def api_submit_review():
    data = request.get_json() or {}
    pid = data.get("product_id")
    name = data.get("customer_name")
    city = data.get("city")
    rating = data.get("rating")
    text = data.get("review_text")

    if not all([pid, name, city, rating, text]):
        return jsonify({"success": False, "error": "All review fields are required."}), 400

    rev_id = database.add_review(pid, name, city, rating, text)
    return jsonify({"success": True, "message": "Review submitted successfully! Thank you for sharing your experience with ISVANTE.", "review_id": rev_id})

@app.route("/api/ai/chat", methods=["POST"])
def api_ai_chat():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    history = data.get("history", [])

    if not user_message:
        return jsonify({"success": False, "error": "Message is empty."}), 400

    reply = ai_concierge.handle_chat_message(user_message, history)
    return jsonify({"success": True, "reply": reply})

# ==========================================
# ADMIN REST APIS
# ==========================================

@app.route("/api/admin/stats", methods=["GET"])
@admin_required
def api_admin_stats():
    conn = database.get_db()
    total_sales = conn.execute("SELECT COALESCE(SUM(total), 0) as s FROM orders WHERE order_status != 'Cancelled'").fetchone()["s"]
    total_orders = conn.execute("SELECT COUNT(*) as c FROM orders").fetchone()["c"]
    pending_orders = conn.execute("SELECT COUNT(*) as c FROM orders WHERE order_status = 'Pending'").fetchone()["c"]
    total_products = conn.execute("SELECT COUNT(*) as c FROM products").fetchone()["c"]
    low_stock = conn.execute("SELECT COUNT(*) as c FROM products WHERE stock < 5").fetchone()["c"]
    
    # Recent orders
    recent_orders = conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 10").fetchall()
    conn.close()

    return jsonify({
        "success": True,
        "stats": {
            "total_sales": total_sales,
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "total_products": total_products,
            "low_stock": low_stock
        },
        "recent_orders": [dict(o) for o in recent_orders]
    })

@app.route("/api/admin/orders", methods=["GET"])
@admin_required
def api_admin_get_orders():
    status = request.args.get("status")
    search = request.args.get("search")
    
    conn = database.get_db()
    query = "SELECT * FROM orders WHERE 1=1"
    params = []

    if status and status != "all":
        query += " AND order_status = ?"
        params.append(status)

    if search:
        query += " AND (order_number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? OR city LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])

    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    
    orders = []
    for r in rows:
        ord_d = dict(r)
        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (ord_d["id"],)).fetchall()
        ord_d["items"] = [dict(it) for it in items]
        orders.append(ord_d)

    conn.close()
    return jsonify({"success": True, "orders": orders})

@app.route("/api/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def api_admin_update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get("order_status")
    courier = data.get("courier_name")
    tracking = data.get("tracking_number")

    valid_statuses = ["Pending", "Confirmed", "Processing", "Shipped", "Delivered", "Cancelled"]
    if new_status not in valid_statuses:
        return jsonify({"success": False, "error": "Invalid order status."}), 400

    conn = database.get_db()
    conn.execute("""
    UPDATE orders 
    SET order_status = ?, courier_name = COALESCE(?, courier_name), tracking_number = COALESCE(?, tracking_number), updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (new_status, courier, tracking, order_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": f"Order #{order_id} updated to {new_status}."})

@app.route("/api/admin/products", methods=["POST"])
@admin_required
def api_admin_add_product():
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"success": False, "error": "Product name is required"}), 400

    import re
    slug = re.sub(r"[^\w\s-]", "", name.lower()).strip().replace(" ", "-")
    sku = data.get("sku") or f"ISV-{slug[:6].upper()}"

    conn = database.get_db()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO products (
        name, slug, sku, category_id, price, compare_at_price, is_featured, is_bestseller, is_new_arrival,
        stock, short_description, description, movement, case_material, strap_material,
        dial_size, water_resistance, glass_material, warranty, color, main_image
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name, slug, sku, data.get("category_id"), float(data.get("price", 0)),
        float(data.get("compare_at_price") or 0) or None,
        1 if data.get("is_featured") else 0,
        1 if data.get("is_bestseller") else 0,
        1 if data.get("is_new_arrival") else 0,
        int(data.get("stock", 10)),
        data.get("short_description", ""),
        data.get("description", ""),
        data.get("movement", "Precision Quartz"),
        data.get("case_material", "316L Stainless Steel"),
        data.get("strap_material", "Genuine Leather"),
        data.get("dial_size", "40mm"),
        data.get("water_resistance", "5 ATM"),
        data.get("glass_material", "Sapphire Crystal"),
        data.get("warranty", "1 Year ISVANTE Warranty"),
        data.get("color", "Gold / Black"),
        data.get("main_image", "/static/images/chrono_sovereign.jpg")
    ))
    prod_id = cursor.lastrowid
    
    # Optional gallery images
    gallery = data.get("gallery", [])
    for idx, g_img in enumerate(gallery):
        cursor.execute("INSERT INTO product_images (product_id, image_url, display_order) VALUES (?, ?, ?)", (prod_id, g_img, idx))

    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Product created successfully", "product_id": prod_id, "slug": slug})

@app.route("/api/admin/products/<int:prod_id>", methods=["PUT", "DELETE"])
@admin_required
def api_admin_modify_product(prod_id):
    conn = database.get_db()
    if request.method == "DELETE":
        conn.execute("DELETE FROM products WHERE id = ?", (prod_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Product deleted successfully."})

    data = request.get_json() or {}
    conn.execute("""
    UPDATE products SET
        name = COALESCE(?, name),
        price = COALESCE(?, price),
        compare_at_price = ?,
        stock = COALESCE(?, stock),
        is_featured = COALESCE(?, is_featured),
        is_bestseller = COALESCE(?, is_bestseller),
        is_new_arrival = COALESCE(?, is_new_arrival),
        short_description = COALESCE(?, short_description),
        description = COALESCE(?, description),
        movement = COALESCE(?, movement),
        case_material = COALESCE(?, case_material),
        strap_material = COALESCE(?, strap_material),
        water_resistance = COALESCE(?, water_resistance),
        main_image = COALESCE(?, main_image)
    WHERE id = ?
    """, (
        data.get("name"),
        data.get("price"),
        data.get("compare_at_price"),
        data.get("stock"),
        data.get("is_featured"),
        data.get("is_bestseller"),
        data.get("is_new_arrival"),
        data.get("short_description"),
        data.get("description"),
        data.get("movement"),
        data.get("case_material"),
        data.get("strap_material"),
        data.get("water_resistance"),
        data.get("main_image"),
        prod_id
    ))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Product updated successfully."})

@app.route("/api/admin/settings", methods=["POST"])
@admin_required
def api_admin_save_settings():
    data = request.get_json() or {}
    for k, v in data.items():
        database.update_setting(k, v)
    return jsonify({"success": True, "message": "Settings updated successfully."})

@app.route("/api/admin/coupons", methods=["GET", "POST"])
@admin_required
def api_admin_coupons():
    conn = database.get_db()
    if request.method == "POST":
        data = request.get_json() or {}
        code = data.get("code", "").strip().upper()
        dtype = data.get("discount_type", "percentage")
        val = float(data.get("discount_value", 10))
        min_v = float(data.get("min_order_value", 0))
        
        conn.execute("""
        INSERT INTO coupons (code, discount_type, discount_value, min_order_value, is_active)
        VALUES (?, ?, ?, ?, 1)
        """, (code, dtype, val, min_v))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Coupon {code} created!"})
        
    rows = conn.execute("SELECT * FROM coupons ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify({"success": True, "coupons": [dict(r) for r in rows]})

@app.route("/api/admin/upload", methods=["POST"])
@admin_required
def api_admin_upload_image():
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    import time
    unique_filename = f"{int(time.time())}_{filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
    file.save(filepath)

    return jsonify({"success": True, "url": f"/static/uploads/{unique_filename}"})

# ==========================================
# SEO & SITEMAP
# ==========================================

@app.route("/robots.txt")
def robots_txt():
    content = "User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: /sitemap.xml\n"
    return content, 200, {"Content-Type": "text/plain"}

@app.route("/sitemap.xml")
def sitemap_xml():
    products = database.get_products()
    categories = database.get_all_categories()
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # Static pages
    for path in ["", "/shop", "/about", "/contact", "/track", "/cart", "/checkout"]:
        xml.append(f'  <url><loc>https://isvante.pk{path}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
        
    # Categories
    for c in categories:
        xml.append(f'  <url><loc>https://isvante.pk/shop?category={c["slug"]}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>')
        
    # Products
    for p in products:
        xml.append(f'  <url><loc>https://isvante.pk/product/{p["slug"]}</loc><changefreq>daily</changefreq><priority>0.9</priority></url>')
        
    xml.append('</urlset>')
    return "\n".join(xml), 200, {"Content-Type": "application/xml"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"==================================================")
    print(f"  ISVANTE HOROLOGY — Server launching on port {port}")
    print(f"  http://localhost:{port}")
    print(f"  Admin Panel: http://localhost:{port}/admin")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=port, debug=True)
