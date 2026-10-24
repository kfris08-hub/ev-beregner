(function () {
  'use strict';
  // The photo and its credit are in the HTML. No API, search or storage is needed.
  const image = document.getElementById('carPhoto');
  const loading = document.getElementById('photoLoading');
  if (!image || !image.getAttribute('src')) return;
  function unavailable() {
    image.style.display = 'none';
    if (loading) {
      loading.style.display = 'block';
      loading.textContent = 'Modelbilledet kunne ikke indlæses. Prøv at genindlæse siden.';
    }
  }
  image.addEventListener('error', unavailable);
  if (image.complete && image.naturalWidth === 0) unavailable();
})();
