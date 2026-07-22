import { mount } from 'svelte'
import { registerSW } from 'virtual:pwa-register'
import './app.css'
import App from './App.svelte'
import { initI18n } from './lib/i18n.js'

// Register the service worker for offline support / installability.
// autoUpdate keeps the cached app in sync with new deployments.
registerSW({ immediate: true })

// Wait for fonts to load before mounting the app
async function waitForFonts() {
  if ('fonts' in document) {
    try {
      await document.fonts.ready
      // Wait for specific fonts to be loaded
      await document.fonts.load('1em VT323')
    } catch (error) {
      console.warn('Font loading error:', error)
      // Continue anyway after a short delay
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
  } else {
    // Fallback for browsers without Font Loading API
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
}

// Initialize i18n and wait for fonts before mounting the app
Promise.all([
  initI18n('en'),
  waitForFonts()
]).then(() => {
  // Mark fonts as loaded
  document.body.classList.add('fonts-loaded')
  mount(App, {
    target: document.getElementById('app'),
  })
})
