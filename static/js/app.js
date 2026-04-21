/**
 * Online Auction System - Frontend JavaScript
 * Handles: Navigation, Countdown Timers, Bidding, Real-time Updates, Tabs
 */

document.addEventListener('DOMContentLoaded', function () {
    initNavigation();
    initCountdownTimers();
    initBidding();
    initTabs();
    initFileUpload();
    initAnimations();
});

// ============================================================
// Navigation Toggle (Mobile)
// ============================================================
function initNavigation() {
    const toggle = document.getElementById('nav-toggle');
    const links = document.getElementById('nav-links');
    if (toggle && links) {
        toggle.addEventListener('click', () => links.classList.toggle('active'));
        // Close menu on link click
        links.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => links.classList.remove('active'));
        });
    }

    // Navbar scroll effect
    window.addEventListener('scroll', () => {
        const navbar = document.getElementById('main-navbar');
        if (navbar) {
            navbar.style.background = window.scrollY > 50
                ? 'rgba(10, 10, 26, 0.95)' : 'rgba(10, 10, 26, 0.85)';
        }
    });
}

// ============================================================
// Countdown Timers
// ============================================================
function initCountdownTimers() {
    // Card timers (auction listing)
    document.querySelectorAll('.auction-timer').forEach(el => {
        const endTime = new Date(el.dataset.end + 'Z');
        updateCardTimer(el, endTime);
        setInterval(() => updateCardTimer(el, endTime), 1000);
    });

    // Detail page countdown
    const countdownEl = document.getElementById('countdown-timer');
    if (countdownEl) {
        let totalSeconds = parseInt(countdownEl.dataset.seconds) || 0;
        setInterval(() => {
            if (totalSeconds <= 0) {
                document.getElementById('cd-days').textContent = '0';
                document.getElementById('cd-hours').textContent = '0';
                document.getElementById('cd-minutes').textContent = '0';
                document.getElementById('cd-seconds').textContent = '0';
                return;
            }
            totalSeconds--;
            const days = Math.floor(totalSeconds / 86400);
            const hours = Math.floor((totalSeconds % 86400) / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;

            document.getElementById('cd-days').textContent = days;
            document.getElementById('cd-hours').textContent = hours;
            document.getElementById('cd-minutes').textContent = minutes;
            document.getElementById('cd-seconds').textContent = seconds;
        }, 1000);
    }
}

function updateCardTimer(el, endTime) {
    const now = new Date();
    const diff = endTime - now;

    if (diff <= 0) {
        el.textContent = 'Ended';
        el.style.color = 'var(--danger)';
        return;
    }

    const days = Math.floor(diff / 86400000);
    const hours = Math.floor((diff % 86400000) / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);

    if (days > 0) {
        el.textContent = `${days}d ${hours}h`;
    } else if (hours > 0) {
        el.textContent = `${hours}h ${minutes}m`;
    } else {
        const seconds = Math.floor((diff % 60000) / 1000);
        el.textContent = `${minutes}m ${seconds}s`;
        el.style.color = 'var(--danger)';
    }
}

// ============================================================
// Bidding System
// ============================================================
function initBidding() {
    const bidBtn = document.getElementById('place-bid-btn');
    if (!bidBtn) return;

    bidBtn.addEventListener('click', async function () {
        const auctionId = this.dataset.auction;
        const amountInput = document.getElementById('bid-amount');
        const amount = parseFloat(amountInput.value);
        const feedback = document.getElementById('bid-feedback');

        if (isNaN(amount) || amount <= 0) {
            showFeedback(feedback, 'Please enter a valid bid amount.', 'danger');
            return;
        }

        bidBtn.disabled = true;
        bidBtn.innerHTML = '<span class="spinner"></span> Placing Bid...';

        try {
            const response = await fetch('/api/place-bid', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ auction_id: parseInt(auctionId), amount: amount })
            });

            const data = await response.json();

            if (data.success) {
                showFeedback(feedback, `✅ ${data.message} New price: $${data.new_price.toFixed(2)}`, 'success');
                // Update price display
                const priceEl = document.getElementById('current-price');
                if (priceEl) priceEl.textContent = `$${data.new_price.toFixed(2)}`;
                // Update bid amount suggestion
                amountInput.value = (data.new_price * 1.05).toFixed(2);
                amountInput.min = data.new_price + 1;

                // Refresh after delay
                setTimeout(() => location.reload(), 2000);
            } else {
                showFeedback(feedback, `❌ ${data.message}`, 'danger');
            }
        } catch (error) {
            showFeedback(feedback, `❌ Network error. Please try again.`, 'danger');
        }

        bidBtn.disabled = false;
        bidBtn.innerHTML = '<i class="fas fa-gavel"></i> Place Bid';
    });

    // Auto-refresh auction status every 10 seconds
    if (typeof AUCTION_ID !== 'undefined') {
        setInterval(async () => {
            try {
                const res = await fetch(`/api/auction-status/${AUCTION_ID}`);
                const data = await res.json();

                const priceEl = document.getElementById('current-price');
                if (priceEl && data.current_price) {
                    priceEl.textContent = `$${data.current_price.toFixed(2)}`;
                }

                if (data.status === 'ended') {
                    location.reload();
                }
            } catch (e) {
                // Silent fail for status check
            }
        }, 10000);
    }
}

function showFeedback(el, message, type) {
    if (!el) return;
    el.innerHTML = `<div class="flash-message flash-${type}" style="position:static;">${message}</div>`;
    setTimeout(() => { if (el) el.innerHTML = ''; }, 5000);
}

// ============================================================
// Tab System
// ============================================================
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function () {
            const tabId = this.dataset.tab;
            // Deactivate all tabs
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            // Activate selected
            this.classList.add('active');
            const panel = document.getElementById(tabId);
            if (panel) panel.classList.add('active');
        });
    });
}

// ============================================================
// File Upload Preview
// ============================================================
function initFileUpload() {
    const fileInput = document.getElementById('image');
    const fileName = document.getElementById('file-name');
    if (fileInput && fileName) {
        fileInput.addEventListener('change', function () {
            if (this.files.length > 0) {
                fileName.textContent = `Selected: ${this.files[0].name}`;
            }
        });
    }
}

// ============================================================
// Scroll Animations
// ============================================================
function initAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-in').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s ease';
        observer.observe(el);
    });
}
