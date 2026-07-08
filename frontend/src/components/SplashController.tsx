import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import SplashScreen from "./SplashScreen";

interface SplashControllerProps {
  children: React.ReactNode;
}

export default function SplashController({ children }: SplashControllerProps) {
  const [showSplash, setShowSplash] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  // If the user starts on any path, we can show the splash screen once.
  // We can skip splash screen if the user is already interacting with the dashboard,
  // but showing it on first load of the application fits the prompt requirements perfectly.
  const handleFinish = () => {
    setShowSplash(false);
    // Navigate smoothly to the City Dashboard.
    // If the user isn't already on the dashboard, navigate there.
    if (location.pathname !== "/") {
      navigate("/", { replace: true });
    }
  };

  if (showSplash) {
    return <SplashScreen onFinish={handleFinish} />;
  }

  return <>{children}</>;
}
