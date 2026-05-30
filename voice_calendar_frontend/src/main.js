import { createApp } from 'vue'
import './assets/styles/global.css'
import App from './App.vue'
import './services/socket' // Initialize socket connection

createApp(App).mount('#app')
