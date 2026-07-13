// ==========================================
// IMAGE MODAL / LIGHTBOX LOGIC
// ==========================================
var modal = document.getElementById("imageModal");
var modalImg = document.getElementById("modalImg");
var imgs = document.querySelectorAll(".execution-log img");
var span = document.querySelector(".close-modal");

if (modal && modalImg) {
    imgs.forEach(function(img) {
        img.onclick = function() {
            modal.style.display = "block";
            modalImg.src = this.src;
        }
    });

    if (span) {
        span.onclick = function() { modal.style.display = "none"; }
    }
    
    window.onclick = function(event) {
        if (event.target == modal) { modal.style.display = "none"; }
    }
}

// ==========================================
// TOP NAVIGATION & MOBILE MENU LOGIC
// ==========================================
var mobileBtn = document.getElementById("mobileMenuBtn");
var navLinks = document.getElementById("navLinks");

if (mobileBtn && navLinks) {
    // Toggle mobile menu
    mobileBtn.onclick = function(e) {
        navLinks.classList.toggle("show");
        e.stopPropagation();
    };

    // Close menu when clicking outside
    window.addEventListener("click", function(e) {
        if (navLinks.classList.contains("show") && e.target !== mobileBtn && !navLinks.contains(e.target)) {
            navLinks.classList.remove("show");
        }
    });

    // Close menu when clicking a mobile link
    var links = navLinks.getElementsByTagName("a");
    for (var i = 0; i < links.length; i++) {
        links[i].onclick = function() {
            navLinks.classList.remove("show");
        };
    }
}

// ==========================================
// HIDE / SHOW MENU LOGIC
// ==========================================
var topNav = document.getElementById("topNav");
var hideMenuBtn = document.getElementById("hideMenuBtn");
var showMenuBtn = document.getElementById("showMenuBtn");

if (hideMenuBtn && topNav && showMenuBtn) {
    // When "Hide" is clicked, slide menu up and show the restore button
    hideMenuBtn.onclick = function(e) {
        e.preventDefault(); // Stop any default link behavior
        e.stopPropagation();
        topNav.classList.add("hidden");
        showMenuBtn.style.display = "block";
    };

    // When "Show Menu" is clicked, slide menu back down and hide button
    showMenuBtn.onclick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        topNav.classList.remove("hidden");
        showMenuBtn.style.display = "none";
    };
}

// ==========================================
// BULLETPROOF SMOOTH SCROLLING
// ==========================================
var navBrand = document.getElementById("navBrand");

// Scroll to top when clicking the brand logo
if (navBrand) {
    navBrand.onclick = function(e) {
        e.preventDefault();
        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    };
}

// Intercept all internal anchor links for smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
    anchor.addEventListener('click', function (e) {
        var targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        var targetElement = document.querySelector(targetId);
        if (targetElement) {
            e.preventDefault(); // Stop the browser from instantly jumping
            
            // Calculate the position, accounting for the 90px sticky header
            var headerOffset = 90; 
            var elementPosition = targetElement.getBoundingClientRect().top;
            var offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            // Glide smoothly to the calculated position
            window.scrollTo({
                top: offsetPosition,
                behavior: "smooth"
            });
        }
    });
});