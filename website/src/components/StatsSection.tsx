import { TrendingUp, Zap, Shield, Clock } from "lucide-react";

const StatsSection = () => {
  const stats = [
    { value: "99.7%", label: "Detection Rate", icon: TrendingUp },
    { value: "50ms", label: "Latency", icon: Zap },
    { value: "10M+", label: "Files Processed", icon: Shield },
    { value: "24/7", label: "Uptime", icon: Clock },
  ];

  return (
    <section className="py-24 px-8">
      <div className="max-w-5xl mx-auto">
        <div className="relative rounded-3xl overflow-hidden">
          {/* Background */}
          <div className="absolute inset-0 bg-gradient-to-br from-card via-card to-secondary/50" />
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-accent/5" />
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />
          
          <div className="relative p-12">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              {stats.map((stat, index) => (
                <div 
                  key={stat.label} 
                  className="text-center opacity-0 animate-fade-in group"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-4 group-hover:bg-primary/20 transition-colors duration-300">
                    <stat.icon className="w-6 h-6 text-primary" />
                  </div>
                  <div className="text-4xl md:text-5xl font-bold gradient-text mb-2 font-mono">
                    {stat.value}
                  </div>
                  <div className="text-sm text-muted-foreground tracking-wide uppercase">
                    {stat.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default StatsSection;
