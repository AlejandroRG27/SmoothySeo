document.addEventListener('DOMContentLoaded', function () {
    const dropdownToggles = document.querySelectorAll('.navbar-nav .dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function (e) {
            if (window.innerWidth <= 768) {
                const dropdownMenu = this.nextElementSibling;
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                
                if (isExpanded) {
                    dropdownMenu.style.display = 'none';
                    this.setAttribute('aria-expanded', 'false');
                } else {
                    // Cerrar otros dropdowns abiertos
                    dropdownToggles.forEach(otherToggle => {
                        if (otherToggle !== toggle) {
                            otherToggle.nextElementSibling.style.display = 'none';
                            otherToggle.setAttribute('aria-expanded', 'false');
                        }
                    });
                    dropdownMenu.style.display = 'block';
                    this.setAttribute('aria-expanded', 'true');
                }
                e.preventDefault(); 
                e.stopPropagation(); 
            }
        });
    });

    // Cerrar dropdowns al hacer clic fuera
    document.addEventListener('click', function (e) {
        if (window.innerWidth <= 768) {
            dropdownToggles.forEach(toggle => {
                const dropdownMenu = toggle.nextElementSibling;
                if (!toggle.contains(e.target) && !dropdownMenu.contains(e.target)) {
                    dropdownMenu.style.display = 'none';
                    toggle.setAttribute('aria-expanded', 'false');
                }
            });
        }
    });
});