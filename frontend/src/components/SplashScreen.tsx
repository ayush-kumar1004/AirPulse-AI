import React, { useEffect } from "react";
import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import ParticleBackground from "./ParticleBackground";
import logo from "../assets/airpulse-logo.png";

interface SplashScreenProps {
  onFinish: () => void;
}

export default function SplashScreen({ onFinish }: SplashScreenProps) {
  // Timer to end the splash screen after 2.5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      onFinish();
    }, 2500);

    return () => clearTimeout(timer);
  }, [onFinish]);

  // Framer Motion Animation Variants
  const fadeInUpVariants = (delay: number) => ({
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 1.2,
        delay,
        ease: [0.16, 1, 0.3, 1],
      },
    },
  });

  return (
    <div className="relative flex flex-col items-center justify-center min-h-screen bg-[#0b1326] text-[#dae2fd] overflow-hidden select-none font-sans">
      {/* Self-contained Particle Background Component */}
      <ParticleBackground />

      {/* Background Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#0b1326] via-transparent to-[#0b1326]/50 pointer-events-none z-0" />

      {/* Central Branding Container */}
      <main className="relative z-10 flex flex-col items-center text-center px-6 max-w-2xl">
        {/* Logo Section */}
        <motion.div
          variants={fadeInUpVariants(0)}
          initial="hidden"
          animate="visible"
          className="mb-16"
        >
          <div className="relative w-80 h-80 md:w-[450px] md:h-[450px] flex items-center justify-center">
            {/* Glowing cyan ring behind logo */}
            <motion.div
              animate={{
                scale: [1, 1.05, 1],
                opacity: [0.6, 1, 0.6],
              }}
              transition={{
                duration: 4,
                ease: "easeInOut",
                repeat: Infinity,
              }}
              className="absolute inset-0 rounded-full bg-[#8aebff]/10 blur-3xl -z-10"
            />
            {/* Logo Image */}
            <motion.img
              animate={{
                scale: [1, 1.03, 1],
              }}
              transition={{
                duration: 4,
                ease: "easeInOut",
                repeat: Infinity,
              }}
              alt="AirPulse AI Premium Logo"
              className="w-full h-full object-contain"
              src={logo}
            />
          </div>
        </motion.div>

        {/* Typography Section */}
        <div className="space-y-4">
          <motion.p
            variants={fadeInUpVariants(0.2)}
            initial="hidden"
            animate="visible"
            className="text-base text-[#bbc9cd] max-w-md mx-auto"
          >
            AI-Powered Urban Air Quality Intelligence
          </motion.p>

          <motion.div
            variants={fadeInUpVariants(0.4)}
            initial="hidden"
            animate="visible"
            className="flex items-center justify-center gap-2 mt-6"
          >
            <span className="text-[11px] font-semibold uppercase tracking-widest text-[#bbc9cd]">Monitoring</span>
            <span className="w-1 h-1 bg-[#8aebff] rounded-full shadow-[0_0_8px_#22d3ee]" />
            <span className="text-[11px] font-semibold uppercase tracking-widest text-[#bbc9cd]">Predicting</span>
            <span className="w-1 h-1 bg-[#8aebff] rounded-full shadow-[0_0_8px_#22d3ee]" />
            <span className="text-[11px] font-semibold uppercase tracking-widest text-[#bbc9cd]">Protecting</span>
          </motion.div>
        </div>

        {/* Progress Indicator */}
        <motion.div
          variants={fadeInUpVariants(0.6)}
          initial="hidden"
          animate="visible"
          className="mt-16 w-64 md:w-80 space-y-2"
        >
          {/* Scanning Progress Line */}
          <div className="relative h-[2px] w-full rounded-full bg-gradient-to-r from-transparent via-[#22d3ee] to-transparent overflow-hidden">
            <motion.div
              className="absolute top-0 h-full w-full bg-gradient-to-r from-transparent via-white to-transparent"
              initial={{ left: "-100%" }}
              animate={{ left: "100%" }}
              transition={{
                duration: 2,
                ease: "linear",
                repeat: Infinity,
              }}
            />
          </div>

          {/* Status Text with Lucide Icon */}
          <div className="flex items-center justify-center gap-1">
            <TrendingUp className="w-3.5 h-3.5 text-[#8aebff] animate-pulse" />
            <p className="text-xs text-[#bbc9cd]/70 italic">
              Analyzing Delhi's Air Quality...
            </p>
          </div>
        </motion.div>
      </main>

      {/* Footer Identity */}
      <motion.footer
        variants={fadeInUpVariants(0.8)}
        initial="hidden"
        animate="visible"
        className="fixed bottom-0 left-0 right-0 p-6 z-10 flex flex-col md:flex-row items-center justify-between pointer-events-none"
      >
        <div className="hidden md:block" />
        <div className="text-center md:absolute md:left-1/2 md:-translate-x-1/2 space-y-1">
          <p className="text-[11px] font-semibold text-[#bbc9cd]/40 uppercase tracking-widest">
            ET AI Hackathon 2026
          </p>
          <p className="text-[13px] text-[#bbc9cd]/30 font-light">
            Powered by AI • Real-time Environmental Intelligence
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <p className="text-[11px] font-semibold text-[#bbc9cd]/20">
            v1.0
          </p>
        </div>
      </motion.footer>
    </div>
  );
}
