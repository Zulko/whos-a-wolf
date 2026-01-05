import { mount } from 'svelte'
import './app.css'
import App from './App.svelte'
import { initI18n } from './lib/i18n.js'

// Initialize i18n before mounting the app
initI18n('en').then(() => {
  mount(App, {
    target: document.getElementById('app'),
  })
})
