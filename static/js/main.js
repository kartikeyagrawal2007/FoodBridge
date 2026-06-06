// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-hide flash messages
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade-out');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 4000);
    });

    // 2. Client-side filter auto-submit
    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        const selects = filterForm.querySelectorAll('select');
        selects.forEach(select => {
            select.addEventListener('change', () => {
                filterForm.submit();
            });
        });
    }

    // 3. Confirm dialogs for destructive actions
    const confirmButtons = document.querySelectorAll('.confirm-action');
    confirmButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const message = btn.getAttribute('data-confirm') || "Are you sure you want to proceed?";
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // 4. Expiry countdown timer
    const countdownEls = document.querySelectorAll('.expiry-countdown');
    
    function updateCountdowns() {
        countdownEls.forEach(el => {
            const expiryStr = el.getAttribute('data-expiry');
            if (!expiryStr) return;
            
            // Expected format UTC ISO string or timestamp
            const expiryDate = new Date(expiryStr);
            const now = new Date();
            
            const diffMs = expiryDate - now;
            
            if (diffMs <= 0) {
                el.textContent = "Expired";
                el.classList.add('text-danger');
            } else {
                const hours = Math.floor(diffMs / (1000 * 60 * 60));
                const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
                
                if (hours > 24) {
                    const days = Math.floor(hours / 24);
                    el.textContent = `${days}d ${hours % 24}h left`;
                } else if (hours > 0) {
                    el.textContent = `${hours}h ${minutes}m left`;
                } else {
                    el.textContent = `${minutes}m left`;
                    el.style.color = 'var(--danger)';
                    el.style.fontWeight = 'bold';
                }
            }
        });
    }

    if (countdownEls.length > 0) {
        updateCountdowns();
        setInterval(updateCountdowns, 30000); // Update every 30 seconds
    }

    // 5. Animated Counter (Count Up)
    const counters = document.querySelectorAll('.count-up');
    
    const countUpObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseFloat(el.getAttribute('data-target'));
                const duration = 2000; // ms
                const steps = 60;
                const stepTime = duration / steps;
                const increment = target / steps;
                let current = 0;
                
                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        el.textContent = Number.isInteger(target) ? target : target.toFixed(1);
                        clearInterval(timer);
                    } else {
                        el.textContent = Number.isInteger(target) ? Math.floor(current) : current.toFixed(1);
                    }
                }, stepTime);
                
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.1 });

    counters.forEach(counter => {
        countUpObserver.observe(counter);
    });
});
