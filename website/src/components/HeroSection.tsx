import { Shield, Sparkles, Play, ArrowRight } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="relative py-32 px-8 overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-primary/8 rounded-full blur-[150px]" />
        <div className="absolute bottom-0 right-0 w-[500px] h-[400px] bg-accent/5 rounded-full blur-[120px]" />
      </div>

      {/* Subtle grid */}
      <div className="absolute inset-0 opacity-[0.015]" style={{
        backgroundImage: `radial-gradient(circle at 1px 1px, hsl(var(--foreground)) 1px, transparent 0)`,
        backgroundSize: '48px 48px'
      }} />

      <div className="relative max-w-6xl mx-auto">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left content */}
          <div className="text-left">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 mb-8 opacity-0 animate-fade-in">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              <span className="text-xs font-medium text-primary tracking-wide">Now with real-time processing</span>
            </div>
            
            {/* Main heading */}
            <h1 
              className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6 opacity-0 animate-fade-in leading-[1.1]"
              style={{ animationDelay: "100ms" }}
            >
              <span className="text-foreground">Content protection</span>
              <br />
              <span className="text-foreground">powered by </span>
              <span className="gradient-text">AegisAI</span>
            </h1>
            
            {/* Subheading */}
            <p 
              className="text-base md:text-lg text-muted-foreground max-w-lg mb-10 leading-relaxed opacity-0 animate-fade-in"
              style={{ animationDelay: "200ms" }}
            >
              Enterprise-grade neural networks that detect and filter inappropriate content across audio and video. Built for families, broadcasters, and platforms that demand precision.
            </p>
            
            {/* CTA buttons */}
            <div 
              className="flex flex-col sm:flex-row gap-4 opacity-0 animate-fade-in"
              style={{ animationDelay: "300ms" }}
            >
              <button className="gradient-button px-6 py-3.5 text-sm flex items-center justify-center gap-2 group">
                <Shield className="w-4 h-4" />
                <span>Start Free Trial</span>
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
              </button>
              <button className="px-6 py-3.5 rounded-xl font-medium text-sm text-foreground border border-border/60 hover:border-primary/30 hover:bg-primary/5 transition-all duration-300 flex items-center justify-center gap-2">
                <Play className="w-4 h-4" />
                <span>Watch Demo</span>
              </button>
            </div>

            {/* Quick stats */}
            <div 
              className="flex items-center gap-8 mt-12 pt-8 border-t border-border/20 opacity-0 animate-fade-in"
              style={{ animationDelay: "400ms" }}
            >
              <div>
                <p className="text-2xl font-bold text-foreground">99.7%</p>
                <p className="text-xs text-muted-foreground">Detection accuracy</p>
              </div>
              <div className="w-px h-10 bg-border/30" />
              <div>
                <p className="text-2xl font-bold text-foreground">&lt;50ms</p>
                <p className="text-xs text-muted-foreground">Processing latency</p>
              </div>
              <div className="w-px h-10 bg-border/30" />
              <div>
                <p className="text-2xl font-bold text-foreground">24/7</p>
                <p className="text-xs text-muted-foreground">Live monitoring</p>
              </div>
            </div>
          </div>

          {/* Right visual */}
          <div 
            className="relative opacity-0 animate-fade-in hidden lg:block"
            style={{ animationDelay: "300ms" }}
          >
            <div className="relative aspect-square max-w-md mx-auto">
              {/* Main visual container */}
              <div className="absolute inset-8 rounded-3xl bg-gradient-to-br from-card via-card to-secondary/50 border border-border/50 overflow-hidden">
                {/* Animated waveform */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex items-end gap-1 h-32 px-8">
                    {Array.from({ length: 24 }).map((_, i) => (
                      <div
                        key={i}
                        className="w-2 bg-gradient-to-t from-primary/40 to-primary rounded-full animate-pulse"
                        style={{
                          height: `${Math.abs(Math.sin(i * 0.4)) * 60 + 30}%`,
                          animationDelay: `${i * 100}ms`,
                          animationDuration: '1.5s',
                        }}
                      />
                    ))}
                  </div>
                </div>
                
                {/* Overlay gradient */}
                <div className="absolute inset-0 bg-gradient-to-t from-card via-transparent to-transparent" />
                
                {/* Status indicator */}
                <div className="absolute bottom-6 left-6 right-6 p-4 rounded-xl bg-background/80 backdrop-blur-sm border border-border/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-medium text-foreground">Content Analysis</span>
                    <span className="text-xs text-primary font-mono">LIVE</span>
                  </div>
                  <div className="h-1.5 bg-secondary rounded-full overflow-hidden">
                    <div className="h-full w-3/4 bg-gradient-to-r from-primary to-accent rounded-full animate-shimmer" 
                         style={{ backgroundSize: '200% 100%' }} />
                  </div>
                </div>
              </div>

              {/* Decorative elements */}
              <div className="absolute top-4 right-4 w-16 h-16 border border-primary/20 rounded-2xl rotate-12" />
              <div className="absolute bottom-4 left-4 w-12 h-12 bg-primary/10 rounded-xl -rotate-12" />
              
              {/* Floating badge */}
              <div className="absolute -top-2 -right-2 px-3 py-1.5 rounded-full bg-card border border-primary/30 shadow-lg">
                <div className="flex items-center gap-1.5">
                  <Sparkles className="w-3 h-3 text-primary" />
                  <span className="text-xs font-medium text-foreground">AI Active</span>
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
