import os

# Safe zero-dependency .env loader
def load_env_file():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

load_env_file()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "isvante-luxury-secret-key-2026-pakistan")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "isvante.db")
    
    # AI Chatbot Configuration
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini") # gemini or openai
    
    # Store Default Settings (can also be overridden in DB)
    DEFAULT_WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER", "+923001234567")
    DEFAULT_CONTACT_PHONE = os.getenv("CONTACT_PHONE", "+92 300 1234567")
    DEFAULT_CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "concierge@isvante.com")
    DEFAULT_SHIPPING_FEE = int(os.getenv("SHIPPING_FEE", "250"))
    DEFAULT_FREE_SHIPPING_THRESHOLD = int(os.getenv("FREE_SHIPPING_THRESHOLD", "5000"))
    
    # Payment Gateways (Ready for Integration)
    PAYMENT_GATEWAY_PROVIDER = os.getenv("PAYMENT_GATEWAY_PROVIDER", "cod_only") # e.g. safepay, jazzcash, easypaisa, payfast
    SAFEPAY_API_KEY = os.getenv("SAFEPAY_API_KEY", "")
    JAZZCASH_MERCHANT_ID = os.getenv("JAZZCASH_MERCHANT_ID", "")
    JAZZCASH_PASSWORD = os.getenv("JAZZCASH_PASSWORD", "")
    EASYPAISA_STORE_ID = os.getenv("EASYPAISA_STORE_ID", "")
