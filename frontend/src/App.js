import React, {useEffect} from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Signup from "./components/Signup";
import Dashboard from "./components/Dashboard";

function App() {
  useEffect(() => {
    window.onbeforeunload = function () {
      fetch("/shutdown", { method: "POST" });
    };
  }, []);
  const isLoggedIn = !!localStorage.getItem("token");

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route
          path="/dashboard"
            element={isLoggedIn ? <AnimatedUI><Dashboard /></AnimatedUI> : <Navigate to="/login" />}
            />

      </Routes>
    </BrowserRouter>
  );
}

export default App;
