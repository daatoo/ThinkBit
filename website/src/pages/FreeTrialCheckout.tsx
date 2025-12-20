import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { CreditCard, CheckCircle2, ShieldCheck, Zap, Lock, Globe, Server } from "lucide-react";
import { useNavigate } from "react-router-dom";

const FreeTrialCheckout = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
      // Redirect after showing success
      setTimeout(() => {
        navigate("/");
      }, 3000);
    }, 2000);
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
        {/* Confetti/Success Animation Background */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/20 via-background to-background animate-pulse" />

        <Card className="w-full max-w-md glass-card border-primary relative z-10 animate-scale-in">
          <CardContent className="pt-6 flex flex-col items-center text-center space-y-4">
            <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center animate-bounce">
              <CheckCircle2 className="w-10 h-10 text-primary" />
            </div>
            <h2 className="text-3xl font-bold gradient-text">Success!</h2>
            <p className="text-muted-foreground">
              Your free trial has been activated. Redirecting you to the dashboard...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background relative overflow-x-hidden selection:bg-primary/30 selection:text-white">
      {/* Background Grid Animation */}
      <div className="fixed inset-0 retro-grid opacity-20 pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-b from-background/50 via-transparent to-background pointer-events-none" />

      {/* Animated Glow Orbs */}
      <div className="fixed top-20 left-20 w-96 h-96 bg-primary/10 rounded-full blur-[120px] animate-pulse" />
      <div className="fixed bottom-20 right-20 w-96 h-96 bg-secondary/10 rounded-full blur-[120px] animate-pulse delay-700" />

      <div className="relative z-10 container mx-auto px-4 py-12 animate-in fade-in zoom-in duration-500">
        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">

          {/* Left Column: Visuals & Benefits */}
          <div className="hidden lg:block space-y-8 sticky top-12">
            <div className="space-y-4">
              <h1 className="text-4xl font-bold tracking-tight lg:text-5xl">
                Start Your <span className="gradient-text glitch-text" data-text="Free Trial">Free Trial</span>
              </h1>
              <p className="text-xl text-muted-foreground">
                Experience the full power of AegisAI. No commitment, cancel anytime.
              </p>
            </div>

            <div className="glass-card p-6 space-y-6 border-secondary/30">
              <h3 className="text-xl font-semibold flex items-center gap-2">
                <ShieldCheck className="text-secondary" />
                What's Included
              </h3>
              <ul className="space-y-4">
                {[
                  "Unlimited Audio Processing",
                  "Advanced Video Analysis",
                  "Real-time Profanity Filtering",
                  "Priority Support",
                  "API Access"
                ].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-muted-foreground">
                    <div className="w-5 h-5 rounded-full bg-secondary/20 flex items-center justify-center shrink-0">
                      <CheckCircle2 className="w-3 h-3 text-secondary" />
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 rounded-xl bg-primary/10 border border-primary/50 shadow-[0_0_30px_-5px_hsl(320,100%,55%,0.3)] backdrop-blur-sm relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <p className="text-base text-white flex items-start gap-3 relative z-10">
                <div className="p-2 rounded-full bg-primary/20 text-primary">
                  <ShieldCheck className="w-5 h-5 animate-pulse" />
                </div>
                <div>
                  <strong className="text-primary text-lg block mb-1">Fast & Secure</strong>
                  <span className="text-gray-100/90 leading-relaxed">Your data is encrypted and processed with industry-leading security standards.</span>
                </div>
              </p>
            </div>
          </div>

          {/* Right Column: Checkout Form */}
          <div className="glass-card p-1">
            <Card className="border-0 bg-transparent shadow-none">
              <CardHeader>
                <CardTitle>Checkout Details</CardTitle>
                <CardDescription>Enter your information to begin.</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Personal Info */}
                  <div className="space-y-4">
                    <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Account Information</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">First Name</Label>
                        <Input id="firstName" placeholder="Jane" required className="bg-background/50 border-input/50 focus:border-primary focus:ring-1 focus:ring-primary transition-all duration-300" />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Last Name</Label>
                        <Input id="lastName" placeholder="Doe" required className="bg-background/50 border-input/50 focus:border-primary focus:ring-1 focus:ring-primary transition-all duration-300" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address</Label>
                      <Input id="email" type="email" placeholder="jane@example.com" required className="bg-background/50 border-input/50 focus:border-primary focus:ring-1 focus:ring-primary transition-all duration-300" />
                    </div>
                  </div>

                  {/* Payment Info */}
                  <div className="space-y-4">
                    <h4 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Payment Method</h4>
                    <Tabs defaultValue="card" className="w-full">
                      <TabsList className="grid w-full grid-cols-2 mb-4 bg-muted/50">
                        <TabsTrigger value="card">Card</TabsTrigger>
                        <TabsTrigger value="paypal">PayPal</TabsTrigger>
                      </TabsList>

                      <TabsContent value="card" className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="cardNumber">Card Number</Label>
                          <div className="relative">
                            <CreditCard className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                            <Input id="cardNumber" placeholder="0000 0000 0000 0000" className="pl-10 bg-background/50 border-input/50 focus:border-primary focus:ring-1 focus:ring-primary transition-all duration-300" />
                          </div>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="space-y-2">
                            <Label htmlFor="expiry">Expiry Date</Label>
                            <Input id="expiry" placeholder="MM/YY" className="bg-background/50 border-input/50 focus:border-primary focus:ring-1 focus:ring-primary transition-all duration-300" />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="cvc">CVC</Label>
                            <Input id="cvc" placeholder="123" className="bg-background/50 border-input/50 focus:border-primary focus:ring-1 focus:ring-primary transition-all duration-300" />
                          </div>
                        </div>
                      </TabsContent>

                      <TabsContent value="paypal">
                        <div className="flex flex-col items-center justify-center p-6 border-2 border-dashed border-muted rounded-lg bg-muted/10">
                          <p className="text-muted-foreground text-center mb-4">
                            You will be redirected to PayPal to complete your purchase securely.
                          </p>
                          <Button variant="outline" className="w-full">
                            Continue with PayPal
                          </Button>
                        </div>
                      </TabsContent>
                    </Tabs>
                  </div>

                  <div className="pt-4">
                    <Button
                      type="submit"
                      className="w-full gradient-button text-lg h-12 relative overflow-hidden group"
                      disabled={loading}
                    >
                      <span className="relative z-10 flex items-center gap-2 justify-center">
                        {loading ? "Processing..." : "Start Free Trial"}
                        {!loading && <Zap className="w-4 h-4 fill-current" />}
                      </span>
                      <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                    </Button>
                    <p className="text-xs text-center text-muted-foreground mt-4">
                      By clicking above, you agree to our Terms of Service and Privacy Policy.
                    </p>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Testimonials Section */}
        <div className="mt-20 space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold">Trusted by <span className="text-primary">Creators</span></h2>
            <p className="text-muted-foreground">Join thousands of others transforming their media.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                name: "Alex Rivera",
                role: "Content Creator",
                quote: "AegisAI completely transformed my workflow. The processing speed is unreal.",
                initials: "AR"
              },
              {
                name: "Sarah Chen",
                role: "Podcast Host",
                quote: "The best investment I've made for my channel. Simple, fast, and reliable.",
                initials: "SC"
              },
              {
                name: "Mike Ross",
                role: "Video Editor",
                quote: "Finally, a tool that actually does what it promises. Worth every penny.",
                initials: "MR"
              }
            ].map((t, i) => (
              <div key={i} className="glass-card p-6 space-y-4 hover:border-primary/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center font-bold text-white">
                    {t.initials}
                  </div>
                  <div>
                    <h4 className="font-semibold text-white">{t.name}</h4>
                    <p className="text-xs text-muted-foreground">{t.role}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-300 italic">"{t.quote}"</p>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Zap key={s} className="w-3 h-3 text-secondary fill-secondary" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-20 max-w-3xl mx-auto space-y-8 pb-20">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold">Frequently Asked <span className="text-secondary">Questions</span></h2>
            <p className="text-muted-foreground">Everything you need to know about the trial.</p>
          </div>

          <Accordion type="single" collapsible className="w-full space-y-4">
            <AccordionItem value="item-1" className="border border-white/10 rounded-lg px-4 bg-white/5 data-[state=open]:border-primary/50 transition-colors">
              <AccordionTrigger className="text-lg hover:no-underline hover:text-primary">
                Is the free trial really free?
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground">
                Yes! You get full access to all premium features for 7 days. You won't be charged until the trial period ends.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-2" className="border border-white/10 rounded-lg px-4 bg-white/5 data-[state=open]:border-primary/50 transition-colors">
              <AccordionTrigger className="text-lg hover:no-underline hover:text-primary">
                Can I cancel anytime?
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground">
                Absolutely. You can cancel your subscription from your dashboard at any time. If you cancel during the trial, you won't be charged.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-3" className="border border-white/10 rounded-lg px-4 bg-white/5 data-[state=open]:border-primary/50 transition-colors">
              <AccordionTrigger className="text-lg hover:no-underline hover:text-primary">
                What payment methods do you accept?
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground">
                We accept all major credit cards (Visa, Mastercard, Amex) and PayPal. All payments are securely processed.
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="item-4" className="border border-white/10 rounded-lg px-4 bg-white/5 data-[state=open]:border-primary/50 transition-colors">
              <AccordionTrigger className="text-lg hover:no-underline hover:text-primary">
                Do I need to install anything?
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground">
                No software installation is required. AegisAI runs entirely in your browser using cloud processing.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>

        {/* Trust Badges Section */}
        <div className="mt-20 pt-10 border-t border-white/10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {[
              { icon: Lock, label: "SSL Encrypted", sub: "256-bit Protection" },
              { icon: Globe, label: "Global CDN", sub: "Lightning Fast" },
              { icon: Server, label: "99.9% Uptime", sub: "Enterprise SLA" },
              { icon: ShieldCheck, label: "GDPR Ready", sub: "Data Compliance" }
            ].map((badge, i) => (
              <div key={i} className="flex flex-col items-center gap-3 p-4 rounded-xl hover:bg-white/5 transition-colors group">
                <div className="w-12 h-12 rounded-full bg-secondary/10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <badge.icon className="w-6 h-6 text-secondary" />
                </div>
                <div>
                  <h4 className="font-semibold text-white">{badge.label}</h4>
                  <p className="text-xs text-muted-foreground">{badge.sub}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default FreeTrialCheckout;
