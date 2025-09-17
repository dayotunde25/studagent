/**
 * Main JavaScript file for Studagent frontend
 */

// Global variables
let currentUser = null;
let csrfToken = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize the application
function initializeApp() {
    setupEventListeners();
    setupAjaxHeaders();
    checkAuthStatus();
    initializeAnimations();
}

// Setup event listeners
function setupEventListeners() {
    // User menu toggle
    const userMenuBtn = document.querySelector('.user-menu-btn');
    if (userMenuBtn) {
        userMenuBtn.addEventListener('click', toggleUserMenu);
    }

    // Mobile menu toggle
    const navToggle = document.querySelector('.nav-toggle');
    if (navToggle) {
        navToggle.addEventListener('click', toggleMobileMenu);
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', closeDropdownsOnClickOutside);

    // Form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });

    // File uploads
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', handleFileSelect);
    });
}

// Setup AJAX headers
function setupAjaxHeaders() {
    // Get CSRF token from meta tag if available
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        csrfToken = csrfMeta.getAttribute('content');
    }

    // Setup default AJAX headers
    $.ajaxSetup({
        headers: {
            'X-CSRF-Token': csrfToken
        },
        beforeSend: function(xhr) {
            showLoading();
        },
        complete: function(xhr, status) {
            hideLoading();
        }
    });
}

// Check authentication status
function checkAuthStatus() {
    // This would typically check with the backend
    // For now, we'll assume the user is authenticated if we have user data
    const userData = document.querySelector('[data-user]');
    if (userData) {
        currentUser = JSON.parse(userData.getAttribute('data-user'));
    }
}

// Initialize animations
function initializeAnimations() {
    // Add fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });

    // Add slide-in animation to navigation items
    const navItems = document.querySelectorAll('.nav-link');
    navItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.05}s`;
        item.classList.add('slide-in');
    });
}

// User menu functions
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    if (navMenu) {
        navMenu.classList.toggle('show');
    }
}

function closeDropdownsOnClickOutside(event) {
    // Close user dropdown
    const userDropdown = document.getElementById('userDropdown');
    const userMenuBtn = document.querySelector('.user-menu-btn');

    if (userDropdown && userMenuBtn && !userMenuBtn.contains(event.target) && !userDropdown.contains(event.target)) {
        userDropdown.classList.remove('show');
    }

    // Close mobile menu
    const navMenu = document.querySelector('.nav-menu');
    const navToggle = document.querySelector('.nav-toggle');

    if (navMenu && navToggle && !navToggle.contains(event.target) && !navMenu.contains(event.target)) {
        navMenu.classList.remove('show');
    }
}

// Form handling
function handleFormSubmit(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const action = form.getAttribute('action') || window.location.pathname;
    const method = form.getAttribute('method') || 'POST';

    // Validate form
    if (!validateForm(form)) {
        return;
    }

    // Submit form
    submitForm(action, method, formData, form);
}

function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });

    // Email validation
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            showFieldError(field, 'Please enter a valid email address');
            isValid = false;
        }
    });

    // Password confirmation
    const password = form.querySelector('input[name="password"]');
    const confirmPassword = form.querySelector('input[name="password_confirm"]');

    if (password && confirmPassword && password.value !== confirmPassword.value) {
        showFieldError(confirmPassword, 'Passwords do not match');
        isValid = false;
    }

    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);

    field.classList.add('error');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'form-error';
    errorDiv.textContent = message;

    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('error');

    const errorDiv = field.parentNode.querySelector('.form-error');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function submitForm(action, method, formData, form) {
    $.ajax({
        url: action,
        type: method,
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            handleFormSuccess(response, form);
        },
        error: function(xhr, status, error) {
            handleFormError(xhr, status, error, form);
        }
    });
}

function handleFormSuccess(response, form) {
    // Show success message
    showToast('Success!', 'Form submitted successfully', 'success');

    // Handle different response types
    if (response.redirect) {
        setTimeout(() => {
            window.location.href = response.redirect;
        }, 1000);
    } else if (response.reload) {
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    } else {
        // Reset form
        form.reset();
    }
}

function handleFormError(xhr, status, error, form) {
    let message = 'An error occurred. Please try again.';

    if (xhr.responseJSON && xhr.responseJSON.detail) {
        message = xhr.responseJSON.detail;
    }

    showToast('Error', message, 'error');
}

// File handling
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!allowedTypes.includes(file.type)) {
        showToast('Error', 'Please select a valid file type (PDF, TXT, DOC, DOCX)', 'error');
        event.target.value = '';
        return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast('Error', 'File size must be less than 10MB', 'error');
        event.target.value = '';
        return;
    }

    // Show file preview
    showFilePreview(file);
}

function showFilePreview(file) {
    const previewContainer = document.getElementById('filePreview');
    if (!previewContainer) return;

    previewContainer.innerHTML = `
        <div class="file-preview">
            <i class="fas fa-file-alt"></i>
            <div class="file-info">
                <h4>${file.name}</h4>
                <p>${formatFileSize(file.size)} • ${file.type}</p>
            </div>
        </div>
    `;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Toast notifications
function showToast(title, message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas fa-${getToastIcon(type)}"></i>
        <div>
            <strong>${title}</strong>
            <p>${message}</p>
        </div>
        <button onclick="this.parentElement.remove()" class="toast-close">
            <i class="fas fa-times"></i>
        </button>
    `;

    toastContainer.appendChild(toast);

    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);

    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return 'check-circle';
        case 'error': return 'exclamation-circle';
        case 'warning': return 'exclamation-triangle';
        default: return 'info-circle';
    }
}

// Loading states
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('show');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('show');
    }
}

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        // Clear any stored tokens
        localStorage.removeItem('access_token');
        sessionStorage.removeItem('access_token');

        // Redirect to login
        window.location.href = '/login';
    }
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

// Export functions for global use
window.showToast = showToast;
window.logout = logout;