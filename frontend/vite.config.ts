import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    // Deduplicate React so @react-three/fiber uses the same instance as the app.
    // Prevents "Cannot read properties of null (reading 'useMemo')" crash.
    dedupe: ['react', 'react-dom', 'react/jsx-runtime'],
    alias: {
      react: path.resolve('./node_modules/react'),
      'react-dom': path.resolve('./node_modules/react-dom'),
    },
  },
  optimizeDeps: {
    include: ['react', 'react-dom', '@react-three/fiber', '@react-three/drei', 'three'],
  },
  server: {
    port: 5173,
    host: true,
  },
})
