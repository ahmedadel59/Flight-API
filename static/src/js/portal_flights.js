/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.FlightPortalWidget = publicWidget.Widget.extend({
    selector: '.o_flight_portal',
    events: {
        'click #syncBtn': '_onSyncFlights',
        'click #saveKey': '_onSaveApiKey',
    },

    /**
     * Sync flights from AviationStack API
     * @param {Event} ev
     */
    async _onSyncFlights(ev) {
        ev.preventDefault();
        const btn = ev.currentTarget;
        const originalHtml = btn.innerHTML;

        btn.disabled = true;
        btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Syncing...';

        try {
            const response = await fetch('/my/flights/sync', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {},
                    id: Math.floor(Math.random() * 1000000),
                }),
            });

            const data = await response.json();

            if (data.error) {
                this._showNotification(data.error.message || 'An error occurred', 'danger');
            } else if (data.result) {
                this._showNotification(data.result.message || 'Sync completed', data.result.success ? 'success' : 'warning');
                if (data.result.success) {
                    setTimeout(() => window.location.reload(), 1000);
                }
            }
        } catch (error) {
            console.error('Sync error:', error);
            this._showNotification('Failed to sync flights. Please try again.', 'danger');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    /**
     * Save API key to system parameters
     * @param {Event} ev
     */
    async _onSaveApiKey(ev) {
        ev.preventDefault();
        const apiKeyInput = this.el.querySelector('#apiKey');
        const apiKey = apiKeyInput ? apiKeyInput.value.trim() : '';

        if (!apiKey) {
            this._showNotification('Please enter an API key', 'warning');
            return;
        }

        try {
            const response = await fetch('/my/flights/set-api-key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: { api_key: apiKey },
                    id: Math.floor(Math.random() * 1000000),
                }),
            });

            const data = await response.json();

            if (data.error) {
                this._showNotification(data.error.message || 'Failed to save API key', 'danger');
            } else if (data.result) {
                this._showNotification(data.result.message || 'API key saved', data.result.success ? 'success' : 'danger');
                if (data.result.success) {
                    this._closeModal('apiModal');
                    apiKeyInput.value = '';
                }
            }
        } catch (error) {
            console.error('Save API key error:', error);
            this._showNotification('Failed to save API key. Please try again.', 'danger');
        }
    },

    /**
     * Close a Bootstrap modal without using bootstrap.Modal directly
     * Uses the close button's click event which Bootstrap handles natively
     * @param {string} modalId - The ID of the modal to close
     */
    _closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            const closeBtn = modal.querySelector('[data-bs-dismiss="modal"]');
            if (closeBtn) {
                closeBtn.click();
            }
        }
    },

    /**
     * Show a notification message to the user
     * @param {string} message - The message to display
     * @param {string} type - Bootstrap alert type (success, danger, warning, info)
     */
    _showNotification(message, type = 'info') {
        // Remove any existing notifications
        const existingAlert = this.el.querySelector('.flight-notification');
        if (existingAlert) {
            existingAlert.remove();
        }

        // Create notification element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show flight-notification`;
        alertDiv.setAttribute('role', 'alert');
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Insert at the top of the container
        const container = this.el.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
        }

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 150);
            }
        }, 5000);
    },
});

export default publicWidget.registry.FlightPortalWidget;
