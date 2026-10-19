/**
 * ISVANTE HOROLOGY — ATELIER ADMIN MANAGEMENT SCRIPT
 */

let allCategories = [];

function switchAdminTab(tabName) {
  document.querySelectorAll('.admin-section').forEach(sec => sec.style.display = 'none');
  document.querySelectorAll('.admin-tab-btn').forEach(btn => btn.classList.remove('active'));

  const activeSec = document.getElementById(`tab-${tabName}`);
  if (activeSec) activeSec.style.display = 'block';

  const buttons = document.querySelectorAll('.admin-tab-btn');
  buttons.forEach(btn => {
    if (btn.getAttribute('onclick').includes(tabName)) {
      btn.classList.add('active');
    }
  });

  if (tabName === 'overview') loadAdminStats();
  if (tabName === 'orders') loadAdminOrders();
  if (tabName === 'products') loadAdminProducts();
  if (tabName === 'coupons') loadAdminCoupons();
  if (tabName === 'settings') loadAdminSettings();
}

async function loadAdminStats() {
  try {
    const res = await fetch('/api/admin/stats');
    const data = await res.json();
    if (data.success) {
      const s = data.stats;
      document.getElementById('kpi-sales').textContent = ISVANTE.formatPKR(s.total_sales);
      document.getElementById('kpi-orders').textContent = s.total_orders;
      document.getElementById('kpi-pending').textContent = s.pending_orders;
      document.getElementById('kpi-products').textContent = s.total_products;
      document.getElementById('kpi-stock').textContent = s.low_stock;

      const tbody = document.getElementById('overview-orders-tbody');
      if (tbody) {
        tbody.innerHTML = data.recent_orders.map(o => `
          <tr>
            <td><strong>#${o.order_number}</strong></td>
            <td>${o.customer_name}</td>
            <td>${o.city}</td>
            <td style="color: var(--gold-light); font-weight: 600;">${ISVANTE.formatPKR(o.total)}</td>
            <td style="text-transform: uppercase; font-size: 0.75rem;">${o.payment_method}</td>
            <td><span class="badge" style="background: ${getStatusBadgeColor(o.order_status)}; color: #000;">${o.order_status}</span></td>
            <td style="color: var(--text-muted); font-size: 0.78rem;">${o.created_at ? o.created_at.substring(0, 16) : ''}</td>
          </tr>
        `).join('');
      }
    }
  } catch (e) {
    console.error('Failed to load stats', e);
  }
}

function getStatusBadgeColor(status) {
  switch (status) {
    case 'Pending': return 'var(--color-warning)';
    case 'Confirmed': return '#38bdf8';
    case 'Processing': return '#a855f7';
    case 'Shipped': return '#f59e0b';
    case 'Delivered': return 'var(--color-success)';
    case 'Cancelled': return 'var(--color-sale)';
    default: return 'var(--gold-primary)';
  }
}

async function loadAdminOrders() {
  const status = document.getElementById('order-status-filter').value;
  const search = document.getElementById('order-search-input').value.trim();

  let url = `/api/admin/orders?status=${status}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    const tbody = document.getElementById('all-orders-tbody');
    if (!tbody) return;

    if (data.success && data.orders.length > 0) {
      tbody.innerHTML = data.orders.map(o => `
        <tr>
          <td>
            <strong>#${o.order_number}</strong>
            <div style="font-size: 0.7rem; color: var(--text-muted);">${o.created_at.substring(0, 16)}</div>
          </td>
          <td>
            <div><strong>${o.customer_name}</strong></div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${o.customer_phone}</div>
            <div style="font-size: 0.72rem; color: var(--gold-light);">${o.customer_email || ''}</div>
          </td>
          <td>
            <div>${o.city}, ${o.province}</div>
            <div style="font-size: 0.72rem; color: var(--text-muted);">${o.address.substring(0, 35)}...</div>
          </td>
          <td>
            <div style="font-size: 0.8rem;">
              ${o.items.map(it => `<div>• ${it.product_name} &times; ${it.quantity}</div>`).join('')}
            </div>
          </td>
          <td style="color: var(--gold-light); font-weight: 700;">
            ${ISVANTE.formatPKR(o.total)}
          </td>
          <td style="text-transform: uppercase; font-size: 0.75rem;">
            ${o.payment_method}
          </td>
          <td>
            <span class="badge" style="background: ${getStatusBadgeColor(o.order_status)}; color: #000;">
              ${o.order_status}
            </span>
          </td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="openOrderStatusModal(${o.id}, '${o.order_number}', '${o.order_status}', '${o.courier_name || ''}', '${o.tracking_number || ''}')" style="padding: 0.4rem 0.8rem; font-size: 0.75rem;">
              Update Status
            </button>
          </td>
        </tr>
      `).join('');
    } else {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 3rem; color: var(--text-muted);">No orders found matching filters.</td></tr>`;
    }
  } catch (e) {
    console.error('Failed to load orders', e);
  }
}

function openOrderStatusModal(id, number, status, courier, tracking) {
  document.getElementById('modal-order-id').value = id;
  document.getElementById('modal-order-title').textContent = `Update Order #${number}`;
  document.getElementById('modal-new-status').value = status;
  document.getElementById('modal-courier-name').value = courier || 'Trax Logistics';
  document.getElementById('modal-tracking-num').value = tracking || '';
  document.getElementById('order-status-modal').classList.add('active');
}

function closeOrderStatusModal() {
  document.getElementById('order-status-modal').classList.remove('active');
}

async function handleSaveOrderStatus(e) {
  e.preventDefault();
  const id = document.getElementById('modal-order-id').value;
  const payload = {
    order_status: document.getElementById('modal-new-status').value,
    courier_name: document.getElementById('modal-courier-name').value.trim(),
    tracking_number: document.getElementById('modal-tracking-num').value.trim()
  };

  try {
    const res = await fetch(`/api/admin/orders/${id}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      ISVANTE.showToast(data.message);
      closeOrderStatusModal();
      loadAdminOrders();
      loadAdminStats();
    } else {
      ISVANTE.showToast(data.error || 'Failed to update order', 'error');
    }
  } catch (e) {
    ISVANTE.showToast('Network error updating order status', 'error');
  }
}

async function loadAdminProducts() {
  try {
    const res = await fetch('/api/products');
    const data = await res.json();
    const tbody = document.getElementById('admin-products-tbody');
    if (!tbody) return;

    if (data.success) {
      tbody.innerHTML = data.products.map(p => `
        <tr>
          <td><img src="${p.main_image}" alt="${p.name}" style="width: 50px; height: 50px; object-fit: cover; border-radius: var(--radius-sm); border: 1px solid var(--border-glass);"></td>
          <td><strong>${p.name}</strong></td>
          <td><code>${p.sku}</code></td>
          <td>${p.category_name || '-'}</td>
          <td style="color: var(--gold-light); font-weight: 600;">${ISVANTE.formatPKR(p.price)}</td>
          <td>
            <span style="color: ${p.stock < 5 ? 'var(--color-sale)' : 'var(--color-success)'}; font-weight: 600;">
              ${p.stock} units
            </span>
          </td>
          <td style="font-size: 0.75rem; color: var(--text-muted);">${p.movement}</td>
          <td>
            <div style="display: flex; gap: 0.5rem;">
              <a href="/product/${p.slug}" target="_blank" class="btn btn-outline btn-sm" style="padding: 0.35rem 0.6rem; font-size: 0.72rem;">View</a>
              <button class="btn btn-sm" onclick="handleDeleteProduct(${p.id})" style="background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.3); padding: 0.35rem 0.6rem; font-size: 0.72rem;">Delete</button>
            </div>
          </td>
        </tr>
      `).join('');
    }
  } catch (e) {
    console.error('Failed to load products', e);
  }
}

function openAddProductModal() {
  document.getElementById('add-product-modal').classList.add('active');
  // Populate categories dropdown
  fetch('/api/categories')
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        allCategories = data.categories;
        const sel = document.getElementById('modal-category-select');
        sel.innerHTML = data.categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
      }
    });
}

function closeAddProductModal() {
  document.getElementById('add-product-modal').classList.remove('active');
}

async function uploadImageFile(fileInput) {
  if (!fileInput.files || fileInput.files.length === 0) return;
  const formData = new FormData();
  formData.append('image', fileInput.files[0]);

  try {
    const res = await fetch('/api/admin/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      document.getElementById('modal-image-url').value = data.url;
      ISVANTE.showToast('Product photograph uploaded successfully.');
    } else {
      ISVANTE.showToast(data.error || 'Upload failed', 'error');
    }
  } catch (e) {
    ISVANTE.showToast('Failed to upload image file.', 'error');
  }
}

async function handleCreateProduct(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    name: form.name.value.trim(),
    price: parseFloat(form.price.value),
    compare_at_price: form.compare_at_price.value ? parseFloat(form.compare_at_price.value) : null,
    stock: parseInt(form.stock.value),
    category_id: parseInt(form.category_id.value),
    movement: form.movement.value.trim(),
    case_material: form.case_material.value.trim(),
    strap_material: form.strap_material.value.trim(),
    water_resistance: form.water_resistance.value.trim(),
    main_image: form.main_image.value.trim(),
    description: form.description.value.trim(),
    is_featured: form.is_featured.checked ? 1 : 0,
    is_bestseller: form.is_bestseller.checked ? 1 : 0,
    is_new_arrival: form.is_new_arrival.checked ? 1 : 0
  };

  try {
    const res = await fetch('/api/admin/products', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      ISVANTE.showToast('Timepiece published to catalog!');
      closeAddProductModal();
      form.reset();
      loadAdminProducts();
      loadAdminStats();
    } else {
      ISVANTE.showToast(data.error || 'Failed to create product', 'error');
    }
  } catch (err) {
    ISVANTE.showToast('Network error creating product', 'error');
  }
}

async function handleDeleteProduct(id) {
  if (!confirm('Are you sure you want to delete this timepiece from the ISVANTE catalog?')) return;

  try {
    const res = await fetch(`/api/admin/products/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      ISVANTE.showToast(data.message);
      loadAdminProducts();
      loadAdminStats();
    } else {
      ISVANTE.showToast(data.error, 'error');
    }
  } catch (e) {
    ISVANTE.showToast('Failed to delete product', 'error');
  }
}

async function loadAdminCoupons() {
  try {
    const res = await fetch('/api/admin/coupons');
    const data = await res.json();
    const tbody = document.getElementById('admin-coupons-tbody');
    if (!tbody) return;

    if (data.success) {
      tbody.innerHTML = data.coupons.map(c => `
        <tr>
          <td><strong><code>${c.code}</code></strong></td>
          <td style="color: var(--color-success); font-weight: 600;">
            ${c.discount_type === 'percentage' ? c.discount_value + '%' : ISVANTE.formatPKR(c.discount_value)}
          </td>
          <td>${c.min_order_value ? ISVANTE.formatPKR(c.min_order_value) : 'None'}</td>
          <td>${c.uses_count} times</td>
          <td><span class="badge ${c.is_active ? 'badge-new' : 'badge-sale'}">${c.is_active ? 'ACTIVE' : 'EXPIRED'}</span></td>
        </tr>
      `).join('');
    }
  } catch (e) {
    console.error('Failed to load coupons', e);
  }
}

async function handleCreateCoupon(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    code: form.code.value.trim(),
    discount_type: form.discount_type.value,
    discount_value: parseFloat(form.discount_value.value),
    min_order_value: form.min_order_value.value ? parseFloat(form.min_order_value.value) : 0
  };

  try {
    const res = await fetch('/api/admin/coupons', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      ISVANTE.showToast(data.message);
      form.reset();
      loadAdminCoupons();
    } else {
      ISVANTE.showToast(data.error, 'error');
    }
  } catch (err) {
    ISVANTE.showToast('Error generating coupon code', 'error');
  }
}

async function loadAdminSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    if (data.success) {
      const s = data.settings;
      document.getElementById('setting-whatsapp').value = s.whatsapp_number || '';
      document.getElementById('setting-phone').value = s.contact_phone || '';
      document.getElementById('setting-email').value = s.contact_email || '';
      document.getElementById('setting-logo').value = s.logo_url || '';
      document.getElementById('setting-shipping').value = s.shipping_fee || '250';
      document.getElementById('setting-threshold').value = s.free_shipping_threshold || '5000';
      document.getElementById('setting-announcement').value = s.announcement_text || '';
      document.getElementById('setting-instagram').value = s.instagram_url || '';
      document.getElementById('setting-facebook').value = s.facebook_url || '';
      document.getElementById('setting-tiktok').value = s.tiktok_url || '';
    }
  } catch (e) {
    console.error('Failed to load settings', e);
  }
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const form = e.target;
  const payload = {
    whatsapp_number: form.whatsapp_number.value.trim(),
    contact_phone: form.contact_phone.value.trim(),
    contact_email: form.contact_email.value.trim(),
    logo_url: form.logo_url.value.trim(),
    shipping_fee: form.shipping_fee.value,
    free_shipping_threshold: form.free_shipping_threshold.value,
    announcement_text: form.announcement_text.value.trim(),
    instagram_url: form.instagram_url.value.trim(),
    facebook_url: form.facebook_url.value.trim(),
    tiktok_url: form.tiktok_url.value.trim()
  };

  try {
    const res = await fetch('/api/admin/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      ISVANTE.showToast(data.message);
    } else {
      ISVANTE.showToast(data.error || 'Failed to update settings', 'error');
    }
  } catch (err) {
    ISVANTE.showToast('Network error saving settings', 'error');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadAdminStats();
});
