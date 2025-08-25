document.addEventListener('DOMContentLoaded', function() {
    const featureItems = document.querySelectorAll('.feature-item');
    const featureImages = document.querySelectorAll('.feature-img');

    featureItems.forEach(item => {
        item.addEventListener('mouseover', function() {
            console.log('Hover on:', this.getAttribute('data-image'));
            const imageKey = this.getAttribute('data-image');
            featureImages.forEach(img => {
                img.classList.remove('active');
                if (img.getAttribute('data-key') === imageKey) {
                    img.classList.add('active');
                }
            });
        });
    });

});
