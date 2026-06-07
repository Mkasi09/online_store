// Custom JavaScript for iPhone Store

document.addEventListener('DOMContentLoaded', function() {
    // Initialize cart functionality
    initializeCart();
    
    // Initialize product interactions
    initializeProductInteractions();
    
    // Initialize form validations
    initializeFormValidations();
    
    // Initialize animations
    initializeAnimations();
});

// Cart functionality
function initializeCart() {
    updateCartCount();
    
    // Auto-update cart count every 5 seconds
    setInterval(updateCartCount, 5000);
}

function updateCartCount() {
    fetch('/cart/summary/')
        .then(response => response.json())
        .then(data => {
            const cartCountElement = document.querySelector('.cart-count');
            if (cartCountElement) {
                cartCountElement.textContent = data.total_items;
                if (data.total_items > 0) {
                    cartCountElement.style.display = 'flex';
                } else {
                    cartCountElement.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error updating cart count:', error));
}

// Product interactions
function initializeProductInteractions() {
    // Add to cart buttons
    const addToCartButtons = document.querySelectorAll('form[action*="add_to_cart"]');
    addToCartButtons.forEach(button => {
        button.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<span class="loading-spinner"></span> Adding...';
                submitButton.disabled = true;
                
                // Re-enable after 2 seconds (in case of redirect issues)
                setTimeout(() => {
                    submitButton.innerHTML = '<i class="fas fa-cart-plus me-1"></i> Add to Cart';
                    submitButton.disabled = false;
                }, 2000);
            }
        });
    });
    
    // Quantity inputs
    const quantityInputs = document.querySelectorAll('input[type="number"][name="quantity"]');
    quantityInputs.forEach(input => {
        input.addEventListener('change', function() {
            const max = parseInt(this.getAttribute('max'));
            const min = parseInt(this.getAttribute('min')) || 1;
            
            if (this.value > max) {
                this.value = max;
                showNotification('Maximum quantity available: ' + max, 'warning');
            }
            if (this.value < min) {
                this.value = min;
            }
        });
    });
}

// Form validations
function initializeFormValidations() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Check required fields
            const requiredFields = this.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            // Check email format
            const emailFields = this.querySelectorAll('input[type="email"]');
            emailFields.forEach(field => {
                if (field.value && !isValidEmail(field.value)) {
                    isValid = false;
                    field.classList.add('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields correctly.', 'danger');
            }
        });
    });
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Animations
function initializeAnimations() {
    // Fade in elements
    const fadeElements = document.querySelectorAll('.product-card, .feature-box');
    fadeElements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add('fade-in');
        }, index * 100);
    });
    
    // Smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Search functionality
function initializeSearch() {
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                const searchValue = this.value.trim();
                if (searchValue.length >= 2 || searchValue.length === 0) {
                    // Auto-submit search form
                    const form = this.closest('form');
                    if (form) {
                        form.submit();
                    }
                }
            }, 500);
        });
    }
}

// Image lazy loading
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Product image gallery (for product detail page)
function initializeProductGallery() {
    const mainImage = document.querySelector('.main-product-image');
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    
    if (mainImage && thumbnails.length > 0) {
        thumbnails.forEach(thumbnail => {
            thumbnail.addEventListener('click', function() {
                const newSrc = this.getAttribute('data-src');
                if (newSrc) {
                    mainImage.src = newSrc;
                    
                    // Update active thumbnail
                    thumbnails.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                }
            });
        });
    }
}

// Filter sidebar toggle for mobile
function initializeMobileFilters() {
    const filterToggle = document.querySelector('.filter-toggle');
    const filterSidebar = document.querySelector('.filter-sidebar');
    
    if (filterToggle && filterSidebar) {
        filterToggle.addEventListener('click', function() {
            filterSidebar.classList.toggle('show');
        });
    }
}

// Price range slider
function initializePriceRange() {
    const priceRange = document.querySelector('#price-range');
    const minPrice = document.querySelector('#min-price');
    const maxPrice = document.querySelector('#max-price');
    
    if (priceRange && minPrice && maxPrice) {
        priceRange.addEventListener('input', function() {
            const value = parseInt(this.value);
            const max = parseInt(this.max);
            const percentage = (value / max) * 100;
            
            this.style.background = `linear-gradient(to right, #667eea 0%, #667eea ${percentage}%, #e9ecef ${percentage}%, #e9ecef 100%)`;
        });
    }
}

// Initialize all functions when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    initializeLazyLoading();
    initializeProductGallery();
    initializeMobileFilters();
    initializePriceRange();
});

// Handle browser back/forward buttons
window.addEventListener('popstate', function(event) {
    if (event.state) {
        // Reload cart count when navigating back
        updateCartCount();
    }
});

// Print functionality
function printPage() {
    window.print();
}

// Share functionality
function shareProduct(url, title) {
    if (navigator.share) {
        navigator.share({
            title: title,
            url: url
        }).catch(err => console.log('Error sharing:', err));
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
            showNotification('Product link copied to clipboard!', 'success');
        });
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) {
                modalInstance.hide();
            }
        });
    }
});
