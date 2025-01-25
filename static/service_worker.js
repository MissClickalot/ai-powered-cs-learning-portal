const VERSION = "v3";  // Update when files in 'static' are changed or when this file is changed
const CACHE_NAME = `cache-${VERSION}`;

const APP_STATIC_RESOURCES = [
   // Use absolute paths for clarity
  "/",                       // Root route (served by Flask - index.html)
  "/static/manifest.json",   // Manifest file
  "/static/icons/scalable.svg", // Icon
  "/static/assets/bootstrap/css/bootstrap.min.css", // Bootstrap CSS file
  "/static/assets/bootstrap/js/bootstrap.min.js", // Bootstrap JS file
];

// Install event to cache these resources
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(APP_STATIC_RESOURCES);
    })
  );
});

// Activate event - Clean up old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME) // Remove old cache versions
          .map((key) => caches.delete(key))
      );
    })
  );
});

// Fetch event to serve cached resources and handle navigation
self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) {
        // Serve the resource from cache
        return response;
      }

      // Handle navigation requests (e.g., offline fallback to index.html)
      if (event.request.mode === "navigate") {
        return caches.match("/");
      }

      // Fetch the resource from the network as a fallback
      return fetch(event.request).catch(() => {
        console.error(`Failed to fetch ${event.request.url}`);
      });
    })
  );
});