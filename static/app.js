// --- CONFIGURACIONES GLOBALES Y DOM ---
const dateInput = document.getElementById('est_delivery_date');
if (dateInput) {
    // Bloquear fechas pasadas (solo hoy o futuro)
    dateInput.min = new Date().toISOString().split("T")[0];
}

let globalCatalog = [];
let shoppingCart = [];

document.addEventListener("DOMContentLoaded", () => {
    checkAuth(); // Al arrancar la app, verifica quién entró
});

// --- SISTEMA DE CONTROL DE ACCESOS Y ROLES ---
const loginOverlay = document.getElementById("loginOverlay");
const loginForm = document.getElementById("loginForm");
const loginMessage = document.getElementById("loginMessage");
const navbar = document.getElementById("navbar");
const mainLayout = document.getElementById("mainLayout");
const userBadge = document.getElementById("userBadge");
const btnLogout = document.getElementById("btnLogout");

const panelVentas = document.getElementById("panelVentas");
const panelAlmacen = document.getElementById("panelAlmacen");

// Evento para el Formulario de Login
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        loginMessage.style.display = "none";

        const payload = {
            username: document.getElementById("username").value,
            password: document.getElementById("password").value
        };

        try {
            const response = await fetch('/api/auth/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                // Guardamos la sesión en el navegador de manera segura y temporal
                localStorage.setItem("userRole", data.role);
                localStorage.setItem("username", data.username);

                loginForm.reset();
                checkAuth(); // Redibujamos la pantalla según el rol
            } else {
                loginMessage.innerText = `❌ ${data.detail}`;
                loginMessage.style.display = "block";
            }
        } catch (error) {
            console.error("Error en login:", error);
        }
    });
}

// Función de verificación de sesión y permisos visuales
function checkAuth() {
    const role = localStorage.getItem("userRole");
    const username = localStorage.getItem("username");

    if (!role) {
        // No hay sesión activa: Mostrar login, ocultar el ERP
        if(loginOverlay) loginOverlay.style.display = "flex";
        if(navbar) navbar.style.display = "none";
        if(mainLayout) mainLayout.style.display = "none";
        return;
    }

    // Hay sesión: Ocultar login, mostrar el ERP
    if(loginOverlay) loginOverlay.style.display = "none";
    if(navbar) navbar.style.display = "flex";
    if(mainLayout) mainLayout.style.display = "grid";
    if(userBadge) userBadge.innerText = `👤 Usuario: ${username} (${role})`;

    // REGLA DE NEGOCIO Y VISUALIZACIÓN POR ROLES
    if (role === "VENDEDOR") {
        if(panelVentas) panelVentas.style.display = "block";
        if(panelAlmacen) panelAlmacen.style.display = "none";
        if(mainLayout) mainLayout.style.gridTemplateColumns = "1fr";
        if(document.getElementById("btnDashboard")) document.getElementById("btnDashboard").style.display = "none"; // Ocultar reporte a vendedor
        loadInventory();
    } else if (role === "ALMACEN") {
        if(panelVentas) panelVentas.style.display = "none";
        if(panelAlmacen) panelAlmacen.style.display = "block";
        if(mainLayout) mainLayout.style.gridTemplateColumns = "1fr";
        if(document.getElementById("btnDashboard")) document.getElementById("btnDashboard").style.display = "block"; // Mostrar reporte al Jefe
        loadInventory();
    }
}

// Botón Cerrar Sesión
if (btnLogout) {
    btnLogout.addEventListener("click", () => {
        localStorage.clear();
        checkAuth();
    });
}


// --- LÓGICA DE INVENTARIO Y CATÁLOGO ---
async function loadInventory() {
    try {
        const response = await fetch('/api/catalog/');
        globalCatalog = await response.json();

        // Solo dibujamos la tabla si el panel de almacén está visible
        if (panelAlmacen && panelAlmacen.style.display !== "none") {
            renderInventoryTable(globalCatalog);
            checkCriticalStock(); // Evaluamos el stock al cargar
        }
    } catch (error) {
        console.error("Error cargando el catálogo:", error);
    }
}

function renderInventoryTable(productsToRender) {
    const tbody = document.querySelector("#inventoryTable tbody");
    if(!tbody) return;
    tbody.innerHTML = "";

    productsToRender.forEach(p => {
        const price = p.unit_price ? parseFloat(p.unit_price).toFixed(2) : "0.00";
        // Si es COMBO, podemos darle un toque visual diferente (opcional)
        const isCombo = p.item_type === "COMBO";

        const row = `<tr style="${isCombo ? 'background-color: #f9f9f9;' : ''}">
            <td>${p.id}</td>
            <td><strong>${p.sku}</strong></td>
            <td>${p.name}</td>
            <td>S/ ${price}</td>
            <td style="color: ${p.stock < 3 ? 'red' : 'green'}; font-weight: bold;">${p.stock} u.</td>
        </tr>`;
        tbody.innerHTML += row;
    });
}

// Buscador interno de la tabla de almacén
const inventorySearchInput = document.getElementById("inventory_search");
if (inventorySearchInput) {
    inventorySearchInput.addEventListener("input", function() {
        const term = this.value.toLowerCase();
        const filteredProducts = globalCatalog.filter(p =>
            p.sku.toLowerCase().includes(term) || p.name.toLowerCase().includes(term)
        );
        renderInventoryTable(filteredProducts);
    });
}


// --- BUSCADOR PREDICTIVO (CARRITO) ---
const searchInput = document.getElementById("product_search");
const hiddenItemId = document.getElementById("item_id");
const autocompleteList = document.getElementById("autocomplete_list");

if (searchInput) {
    searchInput.addEventListener("input", function() {
        const val = this.value.toLowerCase();
        autocompleteList.innerHTML = "";
        hiddenItemId.value = "";

        if (!val) return;

        const matches = globalCatalog.filter(p =>
            p.name.toLowerCase().includes(val) || p.sku.toLowerCase().includes(val)
        );

        matches.forEach(p => {
            const itemDiv = document.createElement("div");
            const stockColor = p.stock < 3 ? 'red' : 'green';
            const stockText = p.stock > 0 ? `${p.stock} disponibles` : 'Agotado';
            const price = p.unit_price ? parseFloat(p.unit_price).toFixed(2) : "0.00";

            itemDiv.innerHTML = `
                <span><strong>${p.sku}</strong> - ${p.name} (S/ ${price})</span>
                <span class="stock-badge" style="color: ${stockColor};">${stockText}</span>
            `;

            itemDiv.addEventListener("click", function() {
                if (p.stock <= 0) {
                    alert("Este ítem está agotado y no se puede añadir.");
                    return;
                }
                hiddenItemId.dataset.price = p.unit_price || 0;
                // Guardamos si es PRODUCTO o COMBO en el HTML
                hiddenItemId.dataset.type = p.item_type;

                searchInput.value = `${p.sku} - ${p.name}`;
                hiddenItemId.value = p.id;
                autocompleteList.innerHTML = "";
            });

            autocompleteList.appendChild(itemDiv);
        });
    });

    document.addEventListener("click", function (e) {
        if (e.target !== searchInput && autocompleteList) {
            autocompleteList.innerHTML = "";
        }
    });
}


// --- LÓGICA DEL CARRITO DE COMPRAS ---
const btnAddCart = document.getElementById("btn_add_cart");
const cartDisplay = document.getElementById("cart_display");

if (btnAddCart) {
    btnAddCart.addEventListener("click", () => {
        const itemId = hiddenItemId.value;
        const itemName = searchInput.value;
        const qty = parseInt(document.getElementById("quantity").value);

        if (!itemId) {
            alert("Por favor, busca y selecciona un ítem de la lista desplegable.");
            return;
        }
        if (qty < 1 || isNaN(qty)) {
            alert("La cantidad debe ser mayor a 0.");
            return;
        }

        const itemPrice = parseFloat(hiddenItemId.dataset.price);

        // Capturamos el tipo que guardamos previamente (COMBO o PRODUCTO)
        const itemType = hiddenItemId.dataset.type || "PRODUCTO";

        // Buscamos asegurándonos de que coincida tanto el ID como el Tipo
        const existingItem = shoppingCart.find(item => item.item_id === parseInt(itemId) && item.item_type === itemType);

        if (existingItem) {
            existingItem.quantity += qty;
        } else {
            shoppingCart.push({
                item_id: parseInt(itemId),
                name: itemName,
                quantity: qty,
                unit_price: itemPrice,
                item_type: itemType
            });
        }

        searchInput.value = "";
        hiddenItemId.value = "";
        document.getElementById("quantity").value = 1;

        renderCart();
    });
}

function renderCart() {
    if(!cartDisplay) return;
    const cartTotalDiv = document.getElementById("cart_total");

    if (shoppingCart.length === 0) {
        cartDisplay.innerHTML = '<div style="color: #888; text-align: center; padding: 10px; font-size: 13px;">El carrito está vacío</div>';
        cartTotalDiv.innerText = "Total a Pagar: S/ 0.00";
        return;
    }

    cartDisplay.innerHTML = "";
    let totalOrder = 0;

    shoppingCart.forEach((item, index) => {
        const lineTotal = item.quantity * item.unit_price;
        totalOrder += lineTotal;

        const div = document.createElement("div");
        div.className = "cart-item";
        div.innerHTML = `
            <span><strong>${item.quantity}x</strong> ${item.name} <span style="color: #666;">(S/ ${lineTotal.toFixed(2)})</span></span>
            <button type="button" class="btn-danger" style="padding: 4px 8px; width: auto; font-size: 12px;" onclick="removeFromCart(${index})">X</button>
        `;
        cartDisplay.appendChild(div);
    });

    cartTotalDiv.innerText = `Total a Pagar: S/ ${totalOrder.toFixed(2)}`;
}

window.removeFromCart = function(index) {
    shoppingCart.splice(index, 1);
    renderCart();
};


// --- CARGA DE EXCEL ---
const excelForm = document.getElementById('excelForm');
if (excelForm) {
    excelForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msgDiv = document.getElementById('excelMessage');
        const fileInput = document.getElementById('excelFile');
        msgDiv.style.display = 'none';

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        const currentRole = localStorage.getItem("userRole");

        try {
            const response = await fetch('/api/inventory/upload-excel/', {
                method: 'POST',
                headers: {
                    'X-User-Role': currentRole
                },
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                msgDiv.className = 'message success';
                msgDiv.innerText = `✅ ${data.detail}`;
                msgDiv.style.display = 'block';
                fileInput.value = '';
                await loadInventory();
            } else {
                msgDiv.className = 'message error';
                msgDiv.innerText = `❌ Error: ${data.detail}`;
                msgDiv.style.display = 'block';
            }
        } catch (error) {
            console.error("Error subiendo Excel:", error);
        }
    });
}


// --- PROCESAR ORDEN (VENTA) ---
const docTypeSelect = document.getElementById('doc_type');
const docInput = document.getElementById('document_number');
const deliverySelect = document.getElementById('delivery_type');
const deliveryFields = document.getElementById('delivery_fields');

if(docTypeSelect) {
    docTypeSelect.addEventListener('change', (e) => {
        docInput.pattern = e.target.value === 'DNI' ? "\\d{8}" : "\\d{11}";
        docInput.placeholder = e.target.value === 'DNI' ? "Ej: 12345678" : "Ej: 10123456789";
    });
}

if(deliverySelect) {
    deliverySelect.addEventListener('change', (e) => {
        if(e.target.value === 'RECOJO') {
            deliveryFields.style.display = 'none';
            document.getElementById('district').removeAttribute('required');
            document.getElementById('address').removeAttribute('required');
        } else {
            deliveryFields.style.display = 'block';
            document.getElementById('district').setAttribute('required', 'true');
            document.getElementById('address').setAttribute('required', 'true');
        }
    });
}

const orderForm = document.getElementById('orderForm');
if (orderForm) {
    orderForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msgDiv = document.getElementById('orderMessage');
        msgDiv.style.display = 'none';

        // 1. Validaciones Frontend Críticas
        if (shoppingCart.length === 0) {
            msgDiv.className = 'message error';
            msgDiv.innerText = `❌ El carrito está vacío. Agrega al menos un ítem.`;
            msgDiv.style.display = 'block';
            return;
        }

        const docType = document.getElementById('doc_type').value;
        const docNum = document.getElementById('document_number').value;

        if (docType === 'DNI' && docNum.length !== 8) {
            msgDiv.className = 'message error';
            msgDiv.innerText = `❌ El DNI debe tener exactamente 8 dígitos.`;
            msgDiv.style.display = 'block';
            return;
        }
        if (docType === 'RUC' && docNum.length !== 11) {
            msgDiv.className = 'message error';
            msgDiv.innerText = `❌ El RUC debe tener exactamente 11 dígitos.`;
            msgDiv.style.display = 'block';
            return;
        }

        // 2. Preparar el Payload
        const itemsToSubmit = shoppingCart.map(item => ({
            item_type: item.item_type,
            item_id: item.item_id,
            quantity: item.quantity
        }));

        const payload = {
            client: {
                doc_type: docType,
                document_number: docNum,
                name: document.getElementById('name').value
            },
            delivery_type: document.getElementById('delivery_type').value,
            district: document.getElementById('district').value || null,
            address: document.getElementById('address').value || null,
            est_delivery_date: document.getElementById('est_delivery_date').value,
            items: itemsToSubmit
        };

        const currentRole = localStorage.getItem("userRole");

        try {
            const response = await fetch('/api/orders/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Role': currentRole
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                msgDiv.className = 'message success';
                msgDiv.innerText = `🎉 Venta procesada exitosamente. Orden ID: ${data.order_id}`;
                msgDiv.style.display = 'block';

                document.getElementById('orderForm').reset();
                shoppingCart = [];
                renderCart();
                if(inventorySearchInput) inventorySearchInput.value = "";

                await loadInventory();
            } else {
                msgDiv.className = 'message error';
                const errorMsg = Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
                msgDiv.innerText = `❌ Fallo en Venta: ${errorMsg}`;
                msgDiv.style.display = 'block';
            }
        } catch (error) {
            console.error("Error procesando orden:", error);
        }
    });
}

// --- SISTEMA DE ALERTAS DE STOCK CRÍTICO ---
let isShowingCriticalOnly = false;
const CRITICAL_THRESHOLD = 5; // Límite para considerar un stock como "Crítico"

function checkCriticalStock() {
    const criticalItems = globalCatalog.filter(p => p.stock < CRITICAL_THRESHOLD);
    const alertBox = document.getElementById("critical_alert_box");
    const countText = document.getElementById("critical_count_text");

    if (alertBox && countText) {
        if (criticalItems.length > 0) {
            alertBox.style.display = "flex";
            countText.innerText = `Hay ${criticalItems.length} producto(s) o combos con stock menor a ${CRITICAL_THRESHOLD} unidades.`;
        } else {
            alertBox.style.display = "none";
        }
    }
}

// Botón para alternar entre "Ver Todo" y "Ver Urgentes"
const btnFilterCritical = document.getElementById("btn_filter_critical");
if (btnFilterCritical) {
    btnFilterCritical.addEventListener("click", () => {
        isShowingCriticalOnly = !isShowingCriticalOnly;

        if (isShowingCriticalOnly) {
            btnFilterCritical.innerText = "Mostrar Todo el Inventario";
            btnFilterCritical.className = "btn-alt";

            const criticalItems = globalCatalog.filter(p => p.stock < CRITICAL_THRESHOLD);
            renderInventoryTable(criticalItems);
        } else {
            btnFilterCritical.innerText = "Ver solo urgentes";
            btnFilterCritical.className = "btn-danger";

            renderInventoryTable(globalCatalog);
            if(document.getElementById("inventory_search")) document.getElementById("inventory_search").value = "";
        }
    });
}