/// <reference types="vite/client" />

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: '@', replacement: path.resolve(__dirname, 'src') }
    ]
  },
  base: './',
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-pdf': ['react-pdf'],
          'pdfjs-dist': ['pdfjs-dist']
        }
      }
    }
  }
})
