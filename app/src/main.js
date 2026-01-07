import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'
import { initI18n } from './lib/i18n.js'

// Wait for fonts to load before mounting the app
async function waitForFonts() {
  if ('fonts' in document) {
    try {
      await document.fonts.ready
      // Wait for specific fonts to be loaded
      await Promise.all([
        document.fonts.load('1em VT323'),
        document.fonts.load('1em "Press Start 2P"')
      ])
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
