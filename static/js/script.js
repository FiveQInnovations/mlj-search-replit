document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const searchButton = document.getElementById('searchButton');
    const spinner = searchButton.querySelector('.spinner-border');

    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            // Show loading state
            searchButton.disabled = true;
            spinner.classList.remove('d-none');
            searchButton.textContent = ' Searching...';
            searchButton.prepend(spinner);
        });
    }
});
