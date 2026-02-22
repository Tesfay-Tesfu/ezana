// ========== HAMBURGER MENU FUNCTIONALITY ==========
document.addEventListener('DOMContentLoaded', function() {
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const navMenu = document.getElementById('navMenu');
    const menuOverlay = document.getElementById('menuOverlay');
    const body = document.body;
    
    if (hamburgerBtn && navMenu && menuOverlay) {
        // Toggle menu function
        function toggleMenu() {
            hamburgerBtn.classList.toggle('open');
            navMenu.classList.toggle('active');
            menuOverlay.classList.toggle('active');
            
            // Prevent body scroll when menu is open
            if (navMenu.classList.contains('active')) {
                body.style.overflow = 'hidden';
            } else {
                body.style.overflow = '';
            }
        }
        
        // Open/close on button click
        hamburgerBtn.addEventListener('click', toggleMenu);
        
        // Close menu when clicking overlay
        menuOverlay.addEventListener('click', toggleMenu);
        
        // Close menu when clicking a nav link (on mobile)
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 992) {
                    toggleMenu();
                }
            });
        });
        
        // Handle window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 992) {
                // Reset menu state on desktop
                hamburgerBtn.classList.remove('open');
                navMenu.classList.remove('active');
                menuOverlay.classList.remove('active');
                body.style.overflow = '';
            }
        });
        
        // Close menu with Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && navMenu.classList.contains('active')) {
                toggleMenu();
            }
        });
    }
});

// ========== HERO CAROUSEL ==========
document.addEventListener('DOMContentLoaded', function() {
    const items = document.querySelectorAll('.carousel-item');
    const titleEl = document.getElementById('hero-title');
    const subtitleEl = document.getElementById('hero-subtitle');
    const buttonEl = document.getElementById('hero-button');
    let currentIndex = 0;
    let interval;
    
    if (items.length > 0) {
        function updateOverlay(index) {
            const activeItem = items[index];
            if (activeItem) {
                if (titleEl) titleEl.textContent = activeItem.dataset.title || 'Experience Authentic Cultural Events';
                if (subtitleEl) subtitleEl.textContent = activeItem.dataset.subtitle || 'Ezana Service brings you the finest diversified services';
                if (buttonEl) {
                    buttonEl.textContent = activeItem.dataset.buttonText || 'Book Now';
                    buttonEl.href = activeItem.dataset.buttonLink || '/booking';
                }
            }
        }
        
        function nextSlide() {
            items[currentIndex].classList.remove('active');
            currentIndex = (currentIndex + 1) % items.length;
            items[currentIndex].classList.add('active');
            updateOverlay(currentIndex);
        }
        
        function prevSlide() {
            items[currentIndex].classList.remove('active');
            currentIndex = (currentIndex - 1 + items.length) % items.length;
            items[currentIndex].classList.add('active');
            updateOverlay(currentIndex);
        }
        
        function startAutoSlide() {
            interval = setInterval(nextSlide, 5000);
        }
        
        function stopAutoSlide() {
            clearInterval(interval);
        }
        
        const prevBtn = document.querySelector('.carousel-control.prev');
        const nextBtn = document.querySelector('.carousel-control.next');
        
        if (prevBtn && nextBtn) {
            prevBtn.addEventListener('click', function() {
                prevSlide();
                stopAutoSlide();
                startAutoSlide();
            });
            
            nextBtn.addEventListener('click', function() {
                nextSlide();
                stopAutoSlide();
                startAutoSlide();
            });
            
            startAutoSlide();
            
            const carousel = document.querySelector('.carousel-container');
            if (carousel) {
                carousel.addEventListener('mouseenter', stopAutoSlide);
                carousel.addEventListener('mouseleave', startAutoSlide);
            }
        }
    }
});

// ========== SMOOTH SCROLLING ==========
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== "#") {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        }
    });
});
