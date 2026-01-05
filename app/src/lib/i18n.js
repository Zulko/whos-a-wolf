import { register, init, getLocaleFromNavigator } from 'svelte-i18n';

register('en', () => import('./locales/en.json'));
register('fr', () => import('./locales/fr.json'));

let initialized = false;

export async function initI18n(locale = null) {
  if (initialized) return;
  
  // Default to 'en' if no locale provided
  const defaultLocale = locale || 'en';
  
  await init({
    fallbackLocale: 'en',
    initialLocale: defaultLocale,
  });
  
  initialized = true;
}

