import { Check, Shield, Zap } from "lucide-react";
import { SignUpModal } from "./AuthModals";

const PricingSection = () => {
  return (
    <section id="pricing" className="relative py-24 px-8 bg-background/50">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:60px_60px]" />
      <div className="absolute h-full w-full bg-background [mask-image:radial-gradient(ellipse_at_center,transparent_20%,black)] pointer-events-none" />

      <div className="max-w-6xl mx-auto relative">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6 gradient-text">
            Transparent Pricing
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Pay only for what you process. No monthly fees, no hidden costs.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mb-20 max-w-4xl mx-auto">
          {/* Audio Card */}
          <div className="glass-card p-8 flex flex-col relative group hover:border-primary/50 transition-colors duration-300">
             <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Zap className="w-24 h-24 text-primary" />
             </div>

             <h3 className="text-2xl font-bold text-foreground mb-2">Audio Intelligence</h3>
             <div className="flex items-baseline gap-1 mb-6">
               <span className="text-4xl font-mono font-bold text-primary">$0.008</span>
               <span className="text-muted-foreground">/ minute</span>
             </div>

             <p className="text-muted-foreground mb-8">
               Perfect for podcasts, music, and voice content. Powered by state-of-the-art speech recognition.
             </p>

             <ul className="space-y-4 mb-8 flex-1">
               <li className="flex items-center gap-3">
                 <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                   <Check className="w-3 h-3 text-primary" />
                 </div>
                 <span className="text-sm text-muted-foreground">High-fidelity transcription</span>
               </li>
               <li className="flex items-center gap-3">
                 <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                   <Check className="w-3 h-3 text-primary" />
                 </div>
                 <span className="text-sm text-muted-foreground">Context-aware filtering</span>
               </li>
               <li className="flex items-center gap-3">
                 <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                   <Check className="w-3 h-3 text-primary" />
                 </div>
                 <span className="text-sm text-muted-foreground">Profanity detection</span>
               </li>
             </ul>

             <SignUpModal>
               <button className="w-full py-3 rounded-lg border border-primary/50 text-primary font-semibold hover:bg-primary/10 transition-colors">
                 Get Started
               </button>
             </SignUpModal>
          </div>

          {/* Video Card */}
          <div className="glass-card p-8 flex flex-col relative group hover:border-secondary/50 transition-colors duration-300">
             <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                <Shield className="w-24 h-24 text-secondary" />
             </div>

             <h3 className="text-2xl font-bold text-foreground mb-2">Video Protection</h3>
             <div className="flex items-baseline gap-1 mb-6">
               <span className="text-4xl font-mono font-bold text-secondary">$0.020</span>
               <span className="text-muted-foreground">/ minute</span>
             </div>

             <p className="text-muted-foreground mb-8">
               Comprehensive video analysis including audio transcription and visual content safety.
             </p>

             <ul className="space-y-4 mb-8 flex-1">
               <li className="flex items-center gap-3">
                 <div className="w-6 h-6 rounded-full bg-secondary/20 flex items-center justify-center shrink-0">
                   <Check className="w-3 h-3 text-secondary" />
                 </div>
                 <span className="text-sm text-muted-foreground">Frame-by-frame analysis</span>
               </li>
               <li className="flex items-center gap-3">
                 <div className="w-6 h-6 rounded-full bg-secondary/20 flex items-center justify-center shrink-0">
                   <Check className="w-3 h-3 text-secondary" />
                 </div>
                 <span className="text-sm text-muted-foreground">NSFW & Violence detection</span>
               </li>
               <li className="flex items-center gap-3">
                 <div className="w-6 h-6 rounded-full bg-secondary/20 flex items-center justify-center shrink-0">
                   <Check className="w-3 h-3 text-secondary" />
                 </div>
                 <span className="text-sm text-muted-foreground">Includes full Audio Intelligence</span>
               </li>
             </ul>

             <SignUpModal>
               <button className="w-full py-3 rounded-lg border border-secondary/50 text-secondary font-semibold hover:bg-secondary/10 transition-colors">
                 Get Started
               </button>
             </SignUpModal>
          </div>
        </div>

        {/* API Info / Under the Hood */}
        <div id="api" className="glass-card p-8 md:p-12 max-w-4xl mx-auto border-t-4 border-t-primary/50">
          <div className="md:flex items-start justify-between gap-8">
            <div className="mb-8 md:mb-0">
              <h3 className="text-2xl font-bold text-foreground mb-4 flex items-center gap-3">
                <Zap className="w-6 h-6 text-primary" />
                Powered by Industry Leaders
              </h3>
              <p className="text-muted-foreground leading-relaxed max-w-xl">
                We leverage the most advanced AI models available to ensure your content is processed with the highest accuracy and reliability.
              </p>
            </div>

            <div className="space-y-6 shrink-0">
               <div className="flex items-center gap-4 p-4 rounded-lg bg-background/50 border border-border/50">
                 <div className="text-left">
                   <p className="text-sm text-muted-foreground mb-1">Visual Intelligence</p>
                   <p className="font-bold text-foreground text-lg">Google Vision API</p>
                 </div>
               </div>

               <div className="flex items-center gap-4 p-4 rounded-lg bg-background/50 border border-border/50">
                 <div className="text-left">
                   <p className="text-sm text-muted-foreground mb-1">Audio Intelligence</p>
                   <p className="font-bold text-foreground text-lg">Google Cloud Speech-to-Text</p>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default PricingSection;
