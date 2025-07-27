// Global WebSocket Notifications
class NotificationManager {
    constructor() {
        this.notificationSocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        
        this.initializeConnection();
        this.setupEventListeners();
    }

    initializeConnection() {
        if (!window.user_id || window.user_id === 'None') {
            console.log('User not authenticated, skipping notification WebSocket');
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
        
        try {
            this.notificationSocket = new WebSocket(wsUrl);
            this.setupSocketHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
        }
    }

    setupSocketHandlers() {
        this.notificationSocket.onopen = (e) => {
            console.log('Notification WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
        };

        this.notificationSocket.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleMessage(data);
        };

        this.notificationSocket.onclose = (e) => {
            console.log('Notification WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        };

        this.notificationSocket.onerror = (e) => {
            console.error('WebSocket error:', e);
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'notification':
                this.showNotification(data);
                break;
            case 'unread_count':
                this.updateUnreadCount(data.count);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    showNotification(data) {
        // Show browser notification if permission granted
        if (Notification.permission === 'granted') {
            const notification = new Notification(data.notification_type, {
                body: data.message,
                icon: data.actor?.avatar || '/static/images/default-avatar.png',
                tag: `notification-${data.id}`,
                requireInteraction: false,
                silent: false
            });

            notification.onclick = () => {
                window.focus();
                this.markNotificationAsRead(data.id);
                notification.close();
            };

            // Auto close after 5 seconds
            setTimeout(() => notification.close(), 5000);
        }

        // Show in-app notification
        this.showInAppNotification(data);

        // Update notification badge/counter
        this.updateNotificationDisplay();
    }

    showInAppNotification(data) {
        // Create notification element
        const notificationEl = document.createElement('div');
        notificationEl.className = 'toast notification-toast';
        notificationEl.innerHTML = `
            <div class="toast-header">
                <img src="${data.actor?.avatar || '/static/images/default-avatar.png'}" 
                     class="rounded me-2" alt="Avatar" width="20" height="20">
                <strong class="me-auto">${data.notification_type}</strong>
                <small class="text-muted">now</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${data.message}
            </div>
        `;

        // Add to notification container or create one
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        container.appendChild(notificationEl);

        // Initialize Bootstrap toast
        if (typeof bootstrap !== 'undefined') {
            const toast = new bootstrap.Toast(notificationEl, {
                autohide: true,
                delay: 5000
            });
            toast.show();

            // Remove element after hide
            notificationEl.addEventListener('hidden.bs.toast', () => {
                notificationEl.remove();
            });
        } else {
            // Fallback without Bootstrap
            notificationEl.style.display = 'block';
            setTimeout(() => {
                notificationEl.style.opacity = '0';
                setTimeout(() => notificationEl.remove(), 300);
            }, 5000);
        }
    }

    updateUnreadCount(count) {
        // Update notification badge
        const badge = document.getElementById('notification-badge');
        const countElement = document.getElementById('notification-count');
        
        if (badge) {
            if (count > 0) {
                badge.style.display = 'inline';
                badge.textContent = count > 99 ? '99+' : count;
            } else {
                badge.style.display = 'none';
            }
        }

        if (countElement) {
            countElement.textContent = count;
        }

        // Update page title
        this.updatePageTitle(count);
    }

    updatePageTitle(count) {
        const title = document.title;
        const cleanTitle = title.replace(/^\(\d+\)\s*/, '');
        
        if (count > 0) {
            document.title = `(${count}) ${cleanTitle}`;
        } else {
            document.title = cleanTitle;
        }
    }

    updateConnectionStatus(isConnected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = isConnected ? 'connected' : 'disconnected';
            statusElement.title = isConnected ? 'Connected' : 'Disconnected';
        }
    }

    markNotificationAsRead(notificationId) {
        if (this.isConnected && this.notificationSocket) {
            this.notificationSocket.send(JSON.stringify({
                type: 'mark_read',
                notification_id: notificationId
            }));
        }
    }

    markAllNotificationsAsRead() {
        if (this.isConnected && this.notificationSocket) {
            this.notificationSocket.send(JSON.stringify({
                type: 'mark_all_read'
            }));
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.initializeConnection();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.log('Max reconnect attempts reached');
        }
    }

    setupEventListeners() {
        // Request notification permission on first interaction
        document.addEventListener('click', this.requestNotificationPermission, { once: true });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isConnected) {
                // Page became visible, might want to refresh data
                this.updateNotificationDisplay();
            }
        });

        // Handle mark all as read button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="mark-all-read"]')) {
                e.preventDefault();
                this.markAllNotificationsAsRead();
            }
        });

        // Handle individual notification read
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="mark-read"]')) {
                e.preventDefault();
                const notificationId = e.target.dataset.notificationId;
                if (notificationId) {
                    this.markNotificationAsRead(notificationId);
                }
            }
        });
    }

    requestNotificationPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                console.log('Notification permission:', permission);
            });
        }
    }

    updateNotificationDisplay() {
        // This method can be called to refresh notification displays
        // when the page becomes visible or after certain actions
    }

    disconnect() {
        if (this.notificationSocket) {
            this.notificationSocket.close();
            this.notificationSocket = null;
            this.isConnected = false;
        }
    }
}

// Custom notification toast styles
const notificationStyles = `
    .notification-toast {
        min-width: 300px;
        margin-bottom: 0.5rem;
        background-color: #fff;
        border: 1px solid #dee2e6;
        border-radius: 0.375rem;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    }
    
    .notification-toast .toast-header {
        background-color: #f8f9fa;
        border-bottom: 1px solid #dee2e6;
    }
    
    .notification-toast.show {
        opacity: 1;
    }
    
    #connection-status {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-left: 5px;
    }
    
    #connection-status.connected {
        background-color: #28a745;
    }
    
    #connection-status.disconnected {
        background-color: #dc3545;
    }
`;

// Add styles to head
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);

// Initialize notification manager when DOM is ready
let notificationManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        notificationManager = new NotificationManager();
    });
} else {
    notificationManager = new NotificationManager();
}

// Make it globally available
window.notificationManager = notificationManager;