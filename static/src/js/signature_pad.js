/**
 * FSO Signature Pad – Canvas-based signature capture for the portal.
 * Mobile-friendly, supports mouse and touch input.
 */
(function () {
    'use strict';

    function initSignaturePad() {
        const modal = document.getElementById('signatureModal');
        if (!modal) return;

        const canvas = document.getElementById('signaturePad');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;
        let hasContent = false;
        const placeholder = modal.querySelector('.fso-sig-placeholder');

        // ── Dimensionar canvas ────────────────────────────────────────────────
        function resizeCanvas() {
            const ratio = Math.max(window.devicePixelRatio || 1, 1);
            const width = canvas.offsetWidth;
            const height = canvas.offsetHeight || 200;

            // Guardar contenido previo si existe
            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = canvas.width;
            tempCanvas.height = canvas.height;
            tempCanvas.getContext('2d').drawImage(canvas, 0, 0);

            canvas.width = width * ratio;
            canvas.height = height * ratio;
            ctx.scale(ratio, ratio);

            // Restaurar configuración
            ctx.strokeStyle = '#1a1a1a';
            ctx.lineWidth = 2.5;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            // Restaurar contenido
            if (hasContent) {
                ctx.drawImage(tempCanvas, 0, 0, width, height);
            }
        }

        // ── Obtener posición relativa al canvas ───────────────────────────────
        function getPos(e) {
            const rect = canvas.getBoundingClientRect();
            if (e.touches && e.touches.length > 0) {
                return {
                    x: e.touches[0].clientX - rect.left,
                    y: e.touches[0].clientY - rect.top,
                };
            }
            return {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top,
            };
        }

        // ── Eventos de dibujo ─────────────────────────────────────────────────
        function startDraw(e) {
            isDrawing = true;
            const pos = getPos(e);
            lastX = pos.x;
            lastY = pos.y;
            // Punto individual (click sin mover)
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 1.2, 0, Math.PI * 2);
            ctx.fill();
            e.preventDefault();
        }

        function draw(e) {
            if (!isDrawing) return;
            e.preventDefault();
            const pos = getPos(e);

            ctx.beginPath();
            ctx.moveTo(lastX, lastY);
            ctx.lineTo(pos.x, pos.y);
            ctx.stroke();

            lastX = pos.x;
            lastY = pos.y;
            hasContent = true;

            if (placeholder) {
                placeholder.style.display = 'none';
            }
        }

        function stopDraw() {
            isDrawing = false;
        }

        // Mouse
        canvas.addEventListener('mousedown', startDraw);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDraw);
        canvas.addEventListener('mouseleave', stopDraw);

        // Touch (móvil/tablet)
        canvas.addEventListener('touchstart', startDraw, { passive: false });
        canvas.addEventListener('touchmove', draw, { passive: false });
        canvas.addEventListener('touchend', stopDraw);
        canvas.addEventListener('touchcancel', stopDraw);

        // ── Botón Limpiar ─────────────────────────────────────────────────────
        const clearBtn = document.getElementById('clearSignature');
        if (clearBtn) {
            clearBtn.addEventListener('click', function () {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                hasContent = false;
                if (placeholder) {
                    placeholder.style.display = '';
                }
            });
        }

        // ── Botón Guardar ─────────────────────────────────────────────────────
        const saveBtn = document.getElementById('saveSignature');
        const signatureInput = document.getElementById('signatureData');
        const signedByInput = document.getElementById('signedBy');

        if (saveBtn) {
            saveBtn.addEventListener('click', function () {
                if (!hasContent) {
                    showAlert(modal, 'Por favor dibuje la firma antes de guardar.', 'warning');
                    return;
                }
                const signedBy = signedByInput ? signedByInput.value.trim() : '';
                if (!signedBy) {
                    showAlert(modal, 'Ingrese el nombre del firmante.', 'warning');
                    if (signedByInput) signedByInput.focus();
                    return;
                }

                // Exportar canvas como PNG en base64
                const dataURL = canvas.toDataURL('image/png');
                if (signatureInput) {
                    signatureInput.value = dataURL;
                }

                // Enviar formulario
                const form = document.getElementById('signatureForm');
                if (form) form.submit();
            });
        }

        // ── Redimensionar al abrir el modal ───────────────────────────────────
        modal.addEventListener('shown.bs.modal', function () {
            hasContent = false;
            resizeCanvas();
        });

        // Limpiar al cerrar
        modal.addEventListener('hidden.bs.modal', function () {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            hasContent = false;
            if (placeholder) placeholder.style.display = '';
        });

        window.addEventListener('resize', function () {
            if (modal.classList.contains('show')) {
                resizeCanvas();
            }
        });

        // Init inicial
        resizeCanvas();
    }

    // ── Helper: mostrar alerta inline en el modal ─────────────────────────────
    function showAlert(container, message, type) {
        const existing = container.querySelector('.fso-inline-alert');
        if (existing) existing.remove();

        const div = document.createElement('div');
        div.className = 'alert alert-' + type + ' alert-dismissible fso-inline-alert py-2 mt-2';
        div.innerHTML = message +
            '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"/>';
        const body = container.querySelector('.modal-body');
        if (body) body.insertBefore(div, body.firstChild);
    }

    // ── Inicializar cuando el DOM esté listo ──────────────────────────────────
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSignaturePad);
    } else {
        initSignaturePad();
    }
})();
