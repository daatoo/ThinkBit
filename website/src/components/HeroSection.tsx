import { Shield, Sparkles, Play, ArrowRight } from "lucide-react";
import ParticleNetwork from "@/components/ParticleNetwork";

const HeroSection = () => {
  return (
    <section className="relative py-32 px-8 overflow-hidden min-h-[90vh] flex items-center justify-center">
      {/* Background effects */}
      <div className="absolute inset-0 bg-background pointer-events-none -z-20" />

      {/* Retro Grid */}
      <div className="absolute inset-0 retro-grid opacity-30 pointer-events-none -z-10" />

      {/* Particle Network Animation */}
      <ParticleNetwork />

      <div className="relative max-w-7xl mx-auto w-full z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left content */}
          <div className="text-left">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-card/50 border border-primary/50 mb-8 opacity-0 animate-fade-in transform skew-x-[-10deg]">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
              </span>
              <span className="text-sm font-bold text-primary tracking-wider uppercase transform skew-x-[10deg] text-glow">
                Now with real-time processing
              </span>
            </div>
            
            {/* Main heading */}
            <h1 
              className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 opacity-0 animate-fade-in leading-[1.1] uppercase italic"
              style={{ animationDelay: "100ms", textShadow: "4px 4px 0px #ff00ff" }}
            >
              <span className="text-white drop-shadow-md">Content protection</span>
              <br />
              <span className="text-white drop-shadow-md">powered by </span>
              <span className="gradient-text">AegisAI</span>
            </h1>
            
            {/* Specific requested text */}
            <div className="mb-8 opacity-0 animate-fade-in" style={{ animationDelay: "150ms" }}>
                <p className="text-xl md:text-2xl font-mono text-secondary font-bold text-glow">
                    processed over 1 million requests during the last day
                </p>
            </div>

            {/* Subheading */}
            <p 
              className="text-base md:text-lg text-gray-300 max-w-lg mb-10 leading-relaxed opacity-0 animate-fade-in font-mono"
              style={{ animationDelay: "200ms" }}
            >
              Enterprise-grade neural networks that detect and filter inappropriate content across audio and video. Built for families, broadcasters, and platforms that demand precision.
            </p>
            
            {/* CTA buttons */}
            <div 
              className="flex flex-col sm:flex-row gap-6 opacity-0 animate-fade-in"
              style={{ animationDelay: "300ms" }}
            >
              <button className="gradient-button px-8 py-4 text-base flex items-center justify-center gap-2 group">
                <div className="flex items-center gap-2">
                    <Shield className="w-5 h-5" />
                    <span>Start Free Trial</span>
                    <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
                </div>
              </button>
              <button className="px-8 py-4 font-bold text-base text-white border-2 border-secondary/60 hover:border-secondary hover:bg-secondary/10 transition-all duration-300 flex items-center justify-center gap-2 transform skew-x-[-10deg] hover:shadow-[0_0_15px_rgba(32,226,215,0.5)]">
                <div className="flex items-center gap-2 transform skew-x-[10deg]">
                    <Play className="w-5 h-5 text-secondary" />
                    <span className="text-secondary">Watch Demo</span>
                </div>
              </button>
            </div>

            {/* Quick stats */}
            <div 
              className="flex items-center gap-8 mt-12 pt-8 border-t border-primary/30 opacity-0 animate-fade-in"
              style={{ animationDelay: "400ms" }}
            >
              <div>
                <p className="text-3xl font-bold text-white text-glow">99.7%</p>
                <p className="text-xs text-secondary font-mono uppercase">Detection accuracy</p>
              </div>
              <div className="w-px h-10 bg-primary/50" />
              <div>
                <p className="text-3xl font-bold text-white text-glow">&lt;50ms</p>
                <p className="text-xs text-secondary font-mono uppercase">Processing latency</p>
              </div>
              <div className="w-px h-10 bg-primary/50" />
              <div>
                <p className="text-3xl font-bold text-white text-glow">24/7</p>
                <p className="text-xs text-secondary font-mono uppercase">Live monitoring</p>
              </div>
            </div>
          </div>

          {/* Right visual */}
          <div 
            className="relative opacity-0 animate-fade-in hidden lg:block"
            style={{ animationDelay: "300ms" }}
          >
            <div className="relative aspect-square max-w-md mx-auto transform hover:scale-105 transition-transform duration-500">
              {/* Main visual container */}
              <div className="absolute inset-0 rounded-xl bg-card border-2 border-secondary/50 overflow-hidden shadow-[0_0_30px_rgba(190,34,255,0.2)]">
                {/* Animated waveform */}
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <div className="flex items-end gap-1 h-40 px-8">
                    {Array.from({ length: 24 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-3 bg-gradient-to-t from-primary/20 to-primary rounded-sm animate-pulse"
                        style={{
                          height: `${Math.abs(Math.sin(i * 0.4)) * 70 + 20}%`,
                          animationDelay: `${i * 100}ms`,
                          animationDuration: '1.2s',
                          boxShadow: "0 0 10px #ff00ff"
                        }}
                      />
                    ))}
                  </div>
                </div>
                
                {/* Overlay gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent opacity-80" />
                
                {/* Status indicator */}
                <div className="absolute bottom-6 left-6 right-6 p-4 rounded-none bg-card/90 border border-primary/50 backdrop-blur-sm shadow-[0_0_15px_rgba(32,226,215,0.15)]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-white uppercase font-mono tracking-widest">Content Analysis</span>
                    <span className="text-xs text-primary font-mono animate-pulse">● LIVE</span>
                  </div>
                  <div className="h-2 bg-gray-800 rounded-none overflow-hidden border border-gray-700">
                    <div className="h-full w-3/4 bg-gradient-to-r from-primary to-secondary animate-shimmer"
                         style={{ backgroundSize: '200% 100%' }} />
                  </div>
                </div>
              </div>

              {/* Decorative elements */}
              <div className="absolute -top-4 -right-4 w-20 h-20 border-2 border-primary/40 rounded-none rotate-12 z-[-1]" />
              <div className="absolute -bottom-4 -left-4 w-16 h-16 border-2 border-secondary/40 rounded-none -rotate-12 z-[-1]" />
              
              {/* Floating badge */}
              <div className="absolute -top-6 -right-6 px-4 py-2 bg-black border border-primary shadow-[0_0_15px_#ff00ff] transform rotate-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-primary animate-spin-slow" />
                  <span className="text-xs font-bold text-white uppercase tracking-wider">AI Active</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
