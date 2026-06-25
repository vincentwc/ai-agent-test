// Enhanced Scripts for Additional Elements

document.addEventListener('DOMContentLoaded', function() {
    // Testimonial Slider (Simple Auto-Rotation)
    const testimonials = document.querySelectorAll('.testimonial-card');
    if (testimonials.length > 0) {
        let currentTestimonial = 0;
        
        function rotateTestimonials() {
            testimonials.forEach((testimonial, index) => {
                testimonial.style.opacity = index === currentTestimonial ? '1' : '0.3';
            });
            
            currentTestimonial = (currentTestimonial + 1) % testimonials.length;
        }
        
        // Rotate every 5 seconds
        if (testimonials.length > 1) {
            setInterval(rotateTestimonials, 5000);
            rotateTestimonials(); // Initial rotation
        }
    }
    
    // FAQ Accordion
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        question.addEventListener('click', () => {
            item.classList.toggle('active');
        });
    });
    
    // Newsletter Form Submission
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const emailInput = this.querySelector('.newsletter-input');
            const email = emailInput.value.trim();
            
            if (email && validateEmail(email)) {
                // In a real implementation, you would send this to your server
                alert('Thank you for subscribing to our newsletter!');
                emailInput.value = '';
            } else {
                alert('Please enter a valid email address.');
            }
        });
    }
    
    // Email validation helper
    function validateEmail(email) {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }
    
    // Animation on scroll
    const animateElements = document.querySelectorAll('.animate-fade-in-up');
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    animateElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Smooth scrolling for all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
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
});
