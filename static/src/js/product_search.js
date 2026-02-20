/**
 * FSO Product Search – Autocomplete para búsqueda de productos en el portal.
 */
(function () {
    'use strict';

    function initProductSearch() {
        const modal = document.getElementById('addLineModal');
        if (!modal) return;

        const searchInput = document.getElementById('productSearch');
        const resultsDiv = document.getElementById('productResults');
        const productIdInput = document.getElementById('productId');
        const priceInput = document.getElementById('productPrice');
        const addLineBtn = document.getElementById('btnAddLine');

        if (!searchInput || !resultsDiv || !productIdInput) return;

        let searchTimeout = null;
        let selectedProduct = null;

        // Deshabilitar botón hasta seleccionar producto
        if (addLineBtn) addLineBtn.disabled = true;

        // ── Búsqueda con debounce ─────────────────────────────────────────────
        searchInput.addEventListener('input', function () {
            const query = this.value.trim();
            clearTimeout(searchTimeout);
            selectedProduct = null;
            productIdInput.value = '';
            if (addLineBtn) addLineBtn.disabled = true;

            if (query.length < 2) {
                resultsDiv.innerHTML = '';
                return;
            }

            searchTimeout = setTimeout(function () {
                // Llamada JSON-RPC al endpoint del controlador
                fetch('/my/field-service/products/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        id: 1,
                        params: { query: query },
                    }),
                })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    resultsDiv.innerHTML = '';
                    const products = (data.result && data.result.products) || [];

                    if (products.length === 0) {
                        resultsDiv.innerHTML = '<div class="p-2 text-muted small">Sin resultados para "' +
                            escapeHtml(query) + '"</div>';
                        return;
                    }

                    products.forEach(function (p) {
                        const item = document.createElement('div');
                        item.className = 'fso-product-item';
                        item.innerHTML =
                            '<span class="fw-semibold">' + escapeHtml(p.name) + '</span>' +
                            (p.ref ? '<small class="text-muted ms-2">[' + escapeHtml(p.ref) + ']</small>' : '') +
                            '<span class="float-end text-muted small">' + escapeHtml(p.uom) + '</span>';

                        item.addEventListener('click', function () {
                            selectedProduct = p;
                            searchInput.value = p.name + (p.ref ? ' [' + p.ref + ']' : '');
                            productIdInput.value = p.id;
                            if (priceInput) priceInput.value = p.price.toFixed(2);
                            resultsDiv.innerHTML = '';
                            if (addLineBtn) addLineBtn.disabled = false;
                        });

                        resultsDiv.appendChild(item);
                    });
                })
                .catch(function (err) {
                    console.error('Error buscando productos:', err);
                });
            }, 300);
        });

        // Cerrar resultados al hacer clic fuera
        document.addEventListener('click', function (e) {
            if (!modal.contains(e.target)) {
                resultsDiv.innerHTML = '';
            }
        });

        // Limpiar al cerrar el modal
        modal.addEventListener('hidden.bs.modal', function () {
            searchInput.value = '';
            resultsDiv.innerHTML = '';
            productIdInput.value = '';
            if (priceInput) priceInput.value = '0.00';
            if (addLineBtn) addLineBtn.disabled = true;
            selectedProduct = null;
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(String(text)));
        return div.innerHTML;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initProductSearch);
    } else {
        initProductSearch();
    }
})();
