// Run this in your browser console to clear all caches and storage
// This will help resolve the "Failed to fetch" error

console.log('🧹 Clearing browser cache and storage...');

// Clear localStorage
localStorage.clear();
console.log('✅ localStorage cleared');

// Clear sessionStorage  
sessionStorage.clear();
console.log('✅ sessionStorage cleared');

// Clear all cookies for this domain
document.cookie.split(";").forEach(function(c) { 
    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
});
console.log('✅ Cookies cleared');

// Clear IndexedDB
if ('indexedDB' in window) {
    indexedDB.databases().then(databases => {
        databases.forEach(db => {
            indexedDB.deleteDatabase(db.name);
        });
        console.log('✅ IndexedDB cleared');
    });
}

// Clear Service Worker cache
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(registrations => {
        registrations.forEach(registration => {
            registration.unregister();
        });
        console.log('✅ Service Workers cleared');
    });
}

// Clear Cache API
if ('caches' in window) {
    caches.keys().then(cacheNames => {
        cacheNames.forEach(cacheName => {
            caches.delete(cacheName);
        });
        console.log('✅ Cache API cleared');
    });
}

console.log('🎉 Browser cache and storage cleared!');
console.log('🔄 Please refresh the page (Ctrl+F5 or Cmd+Shift+R)');