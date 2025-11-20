import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { useState } from 'react';
import './index.css'
import Login from './pages/login.jsx'
// import Signup from './pages/signup.jsx'


function App() {
  const [count, setCount] = useState(0)

  return (
        <Routes>
        <Route path="/" element={<Login />} />
        </Routes>
  )
}

export default App