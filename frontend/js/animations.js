// Initialize the AOS (Animate On Scroll) library
document.addEventListener("DOMContentLoaded", () => {
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,        // Animation duration in milliseconds
            easing: 'ease-out-cubic', // Smooth easing function
            once: true,           // Run animation only once when scrolling down
            offset: 50,           // Offset (in px) from the original trigger point
        });
    }
});
