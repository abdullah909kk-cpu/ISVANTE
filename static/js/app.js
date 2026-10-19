/**
 * ISVANTE HOROLOGY — CORE APPLICATION SCRIPT
 * Crafted to Stand Out | Pakistan Launch Edition
 */

const ISVANTE = (function() {
  // Cart state persisted in localStorage
  let cart = JSON.parse(localStorage.getItem('isvante_cart') || '[]');
  let wishlist = JSON.parse(localStorage.getItem('isvante_wishlist') || '[]');
  let storeSettings = null;

  // Format currency in PKR
  function formatPKR(amount) {
    return 'Rs. ' + Math.round(amount).toLocaleString('en-PK');
  }

  // Toast Notification System
  function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg>`;
    if (type === 'error') {
      icon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
    }
    
    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Save and render cart state
  function saveCart() {
    localStorage.setItem('isvante_cart', JSON.stringify(cart));
    renderCartUI();
  }

  function getCart() {
    return cart;
  }

  function addToCart(product, quantity = 1, openDrawer = true) {
    const existing = cart.find(item => item.id === product.id);
    if (existing) {
      existing.quantity += quantity;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        slug: product.slug,
        price: parseFloat(product.price),
        image: product.main_image || product.image,
        quantity: quantity
      });
    }
    saveCart();
    showToast(`${product.name} added to your collection.`);
    if (openDrawer) {
      toggleCartDrawer(true);
    }
  }

  function buyNow(product, quantity = 1) {
    addToCart(product, quantity, false);
    window.location.href = '/checkout';
  }

  function updateQuantity(productId, delta) {
    const item = cart.find(i => i.id === productId);
    if (item) {
      item.quantity += delta;
      if (item.quantity <= 0) {
        removeFromCart(productId);
      } else {
        saveCart();
      }
    }
  }

  function removeFromCart(productId) {
    cart = cart.filter(i => i.id !== productId);
    saveCart();
    showToast('Watch removed from cart.');
  }

  function clearCart() {
    cart = [];
    saveCart();
  }

  function calculateCartTotals() {
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const threshold = storeSettings ? parseFloat(storeSettings.free_shipping_threshold || 5000) : 5000;
    const shippingFee = (subtotal >= threshold || subtotal === 0) ? 0 : (storeSettings ? parseFloat(storeSettings.shipping_fee || 250) : 250);
    const total = subtotal + shippingFee;
    return { subtotal, shippingFee, total, threshold };
  }

  function renderCartUI() {
    const count = cart.reduce((c, i) => c + i.quantity, 0);
    
    // Update badge count everywhere
    document.querySelectorAll('.cart-count-badge').forEach(badge => {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    });

    const drawerItems = document.getElementById('drawer-items');
    const drawerSubtotal = document.getElementById('drawer-subtotal');
    const drawerTotal = document.getElementById('drawer-total');
    const shippingProgressFill = document.getElementById('shipping-progress-fill');
    const shippingProgressText = document.getElementById('shipping-progress-text');

    if (!drawerItems) return;

    if (cart.length === 0) {
      drawerItems.innerHTML = `
        <div style="text-align: center; padding: 4rem 1rem;">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(212,175,55,0.4)" stroke-width="1.5" style="margin: 0 auto 1.5rem;">
            <circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>
          </svg>
          <h4 style="font-family: var(--font-serif); font-size: 1.15rem; margin-bottom: 0.5rem;">Your Cart is Empty</h4>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 2rem;">Discover precision timepieces crafted to stand out.</p>
          <a href="/shop" class="btn btn-primary btn-sm" onclick="ISVANTE.toggleCartDrawer(false)">Explore Collection</a>
        </div>
      `;
      if (drawerSubtotal) drawerSubtotal.textContent = formatPKR(0);
      if (drawerTotal) drawerTotal.textContent = formatPKR(0);
      if (shippingProgressFill) shippingProgressFill.style.width = '0%';
      if (shippingProgressText) shippingProgressText.innerHTML = `Add watches worth <strong>Rs. 5,000</strong> for <strong>Free Nationwide Delivery</strong>.`;
      return;
    }

    const { subtotal, shippingFee, total, threshold } = calculateCartTotals();

    // Render items
    drawerItems.innerHTML = cart.map(item => `
      <div class="cart-item-row">
        <img src="${item.image}" alt="${item.name}" class="cart-item-img">
        <div class="cart-item-details">
          <a href="/product/${item.slug}" class="cart-item-title">${item.name}</a>
          <div class="cart-item-price">${formatPKR(item.price)}</div>
          <div class="qty-controls">
            <button class="qty-btn" onclick="ISVANTE.updateQuantity(${item.id}, -1)">−</button>
            <span class="qty-display">${item.quantity}</span>
            <button class="qty-btn" onclick="ISVANTE.updateQuantity(${item.id}, 1)">+</button>
          </div>
        </div>
        <button class="remove-item-btn" onclick="ISVANTE.removeFromCart(${item.id})" title="Remove item">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>
      </div>
    `).join('');

    if (drawerSubtotal) drawerSubtotal.textContent = formatPKR(subtotal);
    if (drawerTotal) drawerTotal.textContent = formatPKR(total);

    // Free shipping calculation
    if (shippingProgressFill && shippingProgressText) {
      if (subtotal >= threshold) {
        shippingProgressFill.style.width = '100%';
        shippingProgressText.innerHTML = `🎉 <strong>Congratulations!</strong> You qualify for <strong>FREE Nationwide Delivery</strong> across Pakistan!`;
      } else {
        const remaining = threshold - subtotal;
        const pct = Math.min(100, Math.round((subtotal / threshold) * 100));
        shippingProgressFill.style.width = `${pct}%`;
        shippingProgressText.innerHTML = `Add <strong>${formatPKR(remaining)}</strong> more to unlock <strong>FREE Delivery</strong> across Pakistan.`;
      }
    }
  }

  function toggleCartDrawer(open) {
    const drawer = document.getElementById('cart-drawer');
    const backdrop = document.getElementById('drawer-backdrop');
    if (!drawer || !backdrop) return;

    if (open === undefined) {
      open = !drawer.classList.contains('active');
    }

    if (open) {
      drawer.classList.add('active');
      backdrop.classList.add('active');
      document.body.style.overflow = 'hidden';
      renderCartUI();
    } else {
      drawer.classList.remove('active');
      backdrop.classList.remove('active');
      document.body.style.overflow = '';
    }
  }

  // Wishlist toggle
  function toggleWishlist(product, btnElement) {
    const idx = wishlist.findIndex(w => w.id === product.id);
    if (idx >= 0) {
      wishlist.splice(idx, 1);
      showToast(`${product.name} removed from your wishlist.`);
      if (btnElement) btnElement.classList.remove('active');
    } else {
      wishlist.push({
        id: product.id,
        name: product.name,
        slug: product.slug,
        price: product.price,
        image: product.main_image || product.image
      });
      showToast(`${product.name} saved to your wishlist.`);
      if (btnElement) btnElement.classList.add('active');
    }
    localStorage.setItem('isvante_wishlist', JSON.stringify(wishlist));
    updateWishlistBadges();
  }

  function updateWishlistBadges() {
    const count = wishlist.length;
    document.querySelectorAll('.wishlist-count-badge').forEach(badge => {
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    });
  }

  // Fetch settings dynamically
  async function loadSettings() {
    try {
      const res = await fetch('/api/settings');
      const data = await res.json();
      if (data.success) {
        storeSettings = data.settings;
      }
    } catch (e) {
      console.warn('Could not load dynamic settings, using defaults.', e);
    }
    renderCartUI();
  }

  // Mobile menu toggle
  function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu-drawer');
    const backdrop = document.getElementById('mobile-menu-backdrop');
    if (!menu) return;
    menu.classList.toggle('active');
    if (backdrop) backdrop.classList.toggle('active');
  }

  // Initialize event listeners on DOM ready
  document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    updateWishlistBadges();

    // Setup Drawer Backdrop close
    const backdrop = document.getElementById('drawer-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', () => toggleCartDrawer(false));
    }

    // Setup Close Drawer Button
    const closeBtn = document.getElementById('close-drawer-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => toggleCartDrawer(false));
    }

    // Setup Cart Trigger Buttons
    document.querySelectorAll('.cart-drawer-trigger').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        toggleCartDrawer(true);
      });
    });

    // Mobile Menu Triggers
    const mobBtn = document.getElementById('mobile-menu-toggle');
    if (mobBtn) {
      mobBtn.addEventListener('click', toggleMobileMenu);
    }
    const mobClose = document.getElementById('close-mobile-menu');
    if (mobClose) {
      mobClose.addEventListener('click', toggleMobileMenu);
    }

    // Global Newsletter handler
    document.querySelectorAll('.newsletter-form').forEach(form => {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const input = form.querySelector('input[type="email"]');
        if (input && input.value) {
          showToast(`Welcome to the ISVANTE Circle! You will receive exclusive horology releases at ${input.value}.`);
          input.value = '';
        }
      });
    });
  });

  return {
    formatPKR,
    showToast,
    getCart,
    addToCart,
    buyNow,
    updateQuantity,
    removeFromCart,
    clearCart,
    calculateCartTotals,
    toggleCartDrawer,
    toggleWishlist,
    toggleMobileMenu
  };
})();
