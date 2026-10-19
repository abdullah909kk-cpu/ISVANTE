import json
import urllib.request
import urllib.error
import re
from config import Config
import database

SYSTEM_PROMPT_TEMPLATE = """You are the private AI Horology Concierge for ISVANTE (CRAFTED TO STAND OUT), a prestigious luxury watch brand in Pakistan.
Your role is to assist discerning clients with elegance, clarity, and professionalism.

LIVE CATALOG & SPECIFICATIONS:
{catalog_data}

STORE POLICIES & PAKISTAN OPERATIONS:
- Payment: Cash on Delivery (COD) is available across all cities and towns in Pakistan.
- Nationwide Delivery: 2 to 4 working days via premier courier partners (Trax, TCS, Leopard Courier).
- Shipping Charges: Standard delivery is Rs. {shipping_fee}. FREE Delivery on all orders above Rs. {free_shipping_threshold}.
- Warranty: Every ISVANTE timepiece includes an official 1-Year ISVANTE Nationwide Warranty covering movement and manufacturing defects.
- Returns & Exchanges: 7-day hassle-free replacement policy for unworn watches in original packaging.
- Packaging: Every watch arrives in a signature ISVANTE black velvet gift box with an authenticity card and microfibre polishing cloth.
- Human Concierge: Clients can chat directly on WhatsApp at {whatsapp_number}.

STRICT RULES:
1. ONLY reference watches and specifications from the live catalog above. Do NOT invent models or prices.
2. Always quote prices in Pakistani Rupees (PKR / Rs.).
3. If you cannot answer or verify a specific custom request, politely explain and invite the client to speak with a human specialist via WhatsApp: {whatsapp_number}.
4. Maintain a refined, polite, luxury tone reflecting high horology craftsmanship.
"""

def get_live_catalog_text():
    products = database.get_products()
    lines = []
    for p in products:
        lines.append(
            f"- {p['name']} (SKU: {p['sku']}): Price Rs. {int(p['price']):,} (Regular: Rs. {int(p['compare_at_price']):,}). "
            f"Movement: {p['movement']}. Case: {p['case_material']}. Dial Size: {p['dial_size']}. "
            f"Glass: {p['glass_material']}. Water Resistance: {p['water_resistance']}. "
            f"Strap: {p['strap_material']}. Stock: {p['stock']} units."
        )
    return "\n".join(lines)

def answer_with_gemini(user_message, history, api_key):
    catalog_text = get_live_catalog_text()
    settings = database.get_settings()
    sys_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        catalog_data=catalog_text,
        shipping_fee=settings.get("shipping_fee", "250"),
        free_shipping_threshold=settings.get("free_shipping_threshold", "5000"),
        whatsapp_number=settings.get("whatsapp_number", Config.DEFAULT_WHATSAPP_NUMBER)
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    contents = []
    # Add system context
    contents.append({
        "role": "user",
        "parts": [{"text": sys_prompt + "\n\nPlease confirm you understand your role."}]
    })
    contents.append({
        "role": "model",
        "parts": [{"text": "Understood. I am the ISVANTE Horology Concierge. How may I assist you today?"}]
    })

    for h in history[-4:]:
        role = "user" if h.get("sender") == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": h.get("text", "")}]
        })

    contents.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    payload = json.dumps({"contents": contents}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            answer = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return answer
    except Exception as e:
        # Fall back to local engine if network/API fails
        return fallback_intelligent_engine(user_message)

def fallback_intelligent_engine(user_message):
    """
    Intelligent catalog retrieval engine that runs locally with zero external API key.
    Extracts intent, finds matches against live database, and answers accurately.
    """
    msg = user_message.lower().strip()
    settings = database.get_settings()
    products = database.get_products()
    whatsapp_num = settings.get("whatsapp_number", Config.DEFAULT_WHATSAPP_NUMBER)
    shipping_fee = settings.get("shipping_fee", "250")
    free_threshold = settings.get("free_shipping_threshold", "5000")

    # 1. Greetings
    if re.search(r"^(hi|hello|hey|salam|assalam|aoa|good\s(morning|evening|afternoon))", msg):
        return (
            "Greetings and welcome to **ISVANTE Concierge**. "
            "How may I assist you today? I can help you explore our luxury watch collections, "
            "check specifications, verify Cash on Delivery across Pakistan, or track an existing order."
        )

    # 2. Cash on Delivery (COD) inquiries
    if "cod" in msg or "cash on delivery" in msg or "pay on delivery" in msg:
        return (
            "**Yes, Cash on Delivery (COD) is 100% available nationwide across Pakistan!**\n\n"
            "You can place your order online and pay the courier in cash when your luxury timepiece is delivered to your doorstep. "
            "We deliver to Karachi, Lahore, Islamabad, Rawalpindi, Faisalabad, Multan, Peshawar, Quetta, and all other cities."
        )

    # 3. Delivery times / Shipping charges
    if any(k in msg for k in ["delivery time", "shipping time", "how long", "charges", "shipping fee", "delivery charge", "rider"]):
        return (
            f"**ISVANTE Shipping Information:**\n"
            f"- **Delivery Time:** 2 to 4 business days nationwide across Pakistan via Trax and TCS Express.\n"
            f"- **Standard Shipping:** Rs. {shipping_fee}\n"
            f"- **FREE Delivery:** Complimentary on all orders above Rs. {int(float(free_threshold)):,}!\n"
            f"- Each watch arrives securely packed in a reinforced luxury box with tamper-evident seal."
        )

    # 4. Warranty & Authenticity
    if any(k in msg for k in ["warranty", "guarantee", "authentic", "original", "damage", "repair"]):
        return (
            "**Official 1-Year ISVANTE Warranty:**\n"
            "Every authentic ISVANTE timepiece is backed by our comprehensive 1-Year Official Nationwide Warranty covering the movement, "
            "hands, and craftsmanship. Your package includes an embossed ISVANTE Warranty & Authenticity Card stamped with your unique serial number."
        )

    # 5. Returns & Exchange
    if any(k in msg for k in ["return", "exchange", "refund", "replace", "broken", "faulty"]):
        return (
            "**ISVANTE 7-Day Hassle-Free Policy:**\n"
            "If your watch is defective, damaged in transit, or not as expected, you can request an exchange or return within 7 days of delivery. "
            "Items must remain unworn with protective films and the original box intact. Simply message our WhatsApp concierge at "
            f"[{whatsapp_num}](https://wa.me/{whatsapp_num.replace('+', '')}) to initiate."
        )

    # 6. Specific Watch queries (matching product names, movement, dial size, price)
    matched_product = None
    for p in products:
        p_name = p["name"].lower()
        slug = p["slug"].lower()
        if any(term in msg for term in p_name.split() if len(term) > 3) or slug in msg:
            matched_product = p
            break

    if matched_product:
        # Check if asked about price
        if any(k in msg for k in ["price", "cost", "how much", "rate", "kitne"]):
            return (
                f"**{matched_product['name']}** is priced at **Rs. {int(matched_product['price']):,}** "
                f"(Regular: ~~Rs. {int(matched_product['compare_at_price']):,}~~ — Save Rs. {int(matched_product['compare_at_price'] - matched_product['price']):,}).\n\n"
                f"- **Movement:** {matched_product['movement']}\n"
                f"- **Dial Size:** {matched_product['dial_size']}\n"
                f"- **Stock Status:** {'In Stock (' + str(matched_product['stock']) + ' left)' if matched_product['stock'] > 0 else 'Sold Out'}\n\n"
                f"Would you like to [View Watch Details](/product/{matched_product['slug']}) or order via Cash on Delivery?"
            )
        # Asked about specs / movement / glass / water resistance
        if any(k in msg for k in ["spec", "movement", "glass", "sapphire", "water", "atm", "size", "strap", "case", "material"]):
            return (
                f"**Specifications for {matched_product['name']}:**\n"
                f"- **Movement:** {matched_product['movement']}\n"
                f"- **Case:** {matched_product['case_material']}\n"
                f"- **Glass:** {matched_product['glass_material']}\n"
                f"- **Dial Size:** {matched_product['dial_size']}\n"
                f"- **Water Resistance:** {matched_product['water_resistance']}\n"
                f"- **Strap:** {matched_product['strap_material']}\n"
                f"- **Price:** Rs. {int(matched_product['price']):,}\n\n"
                f"You can [examine the full gallery and order here](/product/{matched_product['slug']})."
            )
        # General about this watch
        return (
            f"**{matched_product['name']}**\n"
            f"{matched_product['short_description']}\n\n"
            f"- **Price:** Rs. {int(matched_product['price']):,} (PKR)\n"
            f"- **Movement:** {matched_product['movement']}\n"
            f"- **Case:** {matched_product['case_material']}\n"
            f"- **Water Resistance:** {matched_product['water_resistance']}\n\n"
            f"[Explore {matched_product['name']}](/product/{matched_product['slug']}) or click below to buy now."
        )

    # 7. Ask about available watches / catalog / recommend
    if any(k in msg for k in ["available", "watches", "catalog", "collection", "models", "recommend", "show me", "best watch", "best seller"]):
        lines = ["**Here are ISVANTE's signature luxury timepieces:**\n"]
        for p in products[:5]:
            lines.append(f"• **[{p['name']}](/product/{p['slug']})** — Rs. {int(p['price']):,} ({p['movement']})")
        lines.append(f"\nAll models feature scratch-resistant sapphire glass and 316L stainless steel. [Browse the complete Shop Catalog](/shop).")
        return "\n".join(lines)

    # 8. Order tracking
    if any(k in msg for k in ["track", "my order", "where is my order", "status"]):
        return (
            "**Track Your ISVANTE Order:**\n"
            "You can track your parcel in real-time by visiting our [Order Tracking Page](/track).\n"
            "Simply enter your **Order Number** (e.g. `ISV-12345`) and the phone number used during checkout.\n\n"
            f"Need urgent assistance? Reach our dispatch team directly on WhatsApp: [{whatsapp_num}](https://wa.me/{whatsapp_num.replace('+', '')})."
        )

    # 9. How to place an order
    if any(k in msg for k in ["how to order", "how to buy", "place order", "checkout"]):
        return (
            "**How to Order on ISVANTE:**\n"
            "1. Select your desired watch and click **Add to Cart** or **Buy Now**.\n"
            "2. Head to **Checkout** and provide your delivery address in Pakistan.\n"
            "3. Select **Cash on Delivery (COD)** (or Online Transfer).\n"
            "4. Click **Complete Order**. You will receive an instant order confirmation and a WhatsApp verification message!"
        )

    # 10. WhatsApp or Human assistance
    if any(k in msg for k in ["whatsapp", "human", "talk to someone", "phone", "contact", "agent", "support"]):
        return (
            f"You can connect directly with our human luxury watch specialist on WhatsApp:\n\n"
            f"📲 **WhatsApp:** [{whatsapp_num}](https://wa.me/{whatsapp_num.replace('+', '')})\n"
            f"📞 **Phone:** {settings.get('contact_phone', Config.DEFAULT_CONTACT_PHONE)}\n"
            f"✉️ **Email:** {settings.get('contact_email', Config.DEFAULT_CONTACT_EMAIL)}\n\n"
            f"Our Horology team is available Monday through Saturday, 10:00 AM – 10:00 PM PKT."
        )

    # 11. Polite Fallback with WhatsApp link
    return (
        "I want to make sure you receive exact details. While I cannot confirm that specific request from our standard horology database, "
        "our luxury watch specialists are standing by to assist you personally.\n\n"
        f"👉 **[Click here to Chat on WhatsApp with ISVANTE Support](https://wa.me/{whatsapp_num.replace('+', '')}?text=Hello%20ISVANTE,%20I%20have%20an%20inquiry%20regarding%20your%20watches.)**\n\n"
        "Alternatively, feel free to ask me about our current watch models, prices, COD, or delivery times across Pakistan!"
    )

def handle_chat_message(user_message, history=None):
    if history is None:
        history = []

    # If user provided API key in env, use live Gemini
    if Config.AI_API_KEY and len(Config.AI_API_KEY.strip()) > 5:
        try:
            return answer_with_gemini(user_message, history, Config.AI_API_KEY.strip())
        except Exception:
            return fallback_intelligent_engine(user_message)
    else:
        return fallback_intelligent_engine(user_message)
