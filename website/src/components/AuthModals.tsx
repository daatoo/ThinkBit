import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Lock, Mail, User } from "lucide-react";

interface AuthModalProps {
  children: React.ReactNode;
}

export const SignInModal = ({ children }: AuthModalProps) => {
  const [open, setOpen] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Sign In Attempted");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px] glass-card border-primary/20">
        <DialogHeader>
          <div className="flex justify-center mb-4">
            <div className="flex justify-center mb-4">
              <img src="/logo.png" alt="AegisAI Logo" className="w-12 h-12 object-contain" />
            </div>
          </div>
          <DialogTitle className="text-center text-2xl gradient-text font-bold">Welcome Back</DialogTitle>
          <DialogDescription className="text-center">
            Enter your credentials to access your account
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input id="email" type="email" placeholder="name@example.com" className="pl-10 bg-background/50 border-primary/20 focus:border-primary/50" required />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input id="password" type="password" className="pl-10 bg-background/50 border-primary/20 focus:border-primary/50" required />
            </div>
          </div>
          <Button type="submit" className="w-full gradient-button">
            Sign In
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export const SignUpModal = ({ children }: AuthModalProps) => {
  const [open, setOpen] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Sign Up Attempted");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[425px] glass-card border-secondary/20">
        <DialogHeader>
          <div className="flex justify-center mb-4">
            <div className="flex justify-center mb-4">
              <img src="/logo.png" alt="AegisAI Logo" className="w-12 h-12 object-contain" />
            </div>
          </div>
          <DialogTitle className="text-center text-2xl gradient-text font-bold">Get Started</DialogTitle>
          <DialogDescription className="text-center">
            Create your account to start protecting your family
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <Label htmlFor="signup-name">Full Name</Label>
            <div className="relative">
              <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input id="signup-name" placeholder="John Doe" className="pl-10 bg-background/50 border-secondary/20 focus:border-secondary/50" required />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="signup-email">Email</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input id="signup-email" type="email" placeholder="name@example.com" className="pl-10 bg-background/50 border-secondary/20 focus:border-secondary/50" required />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="signup-password">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input id="signup-password" type="password" className="pl-10 bg-background/50 border-secondary/20 focus:border-secondary/50" required />
            </div>
          </div>
          <Button type="submit" className="w-full gradient-button from-secondary to-teal-500 hover:shadow-secondary/50">
            Create Account
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
};
