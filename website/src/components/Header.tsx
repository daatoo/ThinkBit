import { Shield, Menu } from "lucide-react";
import { useState } from "react";
import { InfoModal } from "./InfoModals";
import { SignInModal, SignUpModal } from "./AuthModals";

const Header = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full">
      {/* Blur backdrop */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-xl border-b border-border/50" />

      <nav className="relative max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-3 group">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/25 group-hover:shadow-primary/40 transition-shadow">
            <Shield className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold gradient-text">AegisAI</span>
        </a>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Features
          </a>
          <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Pricing
          </a>

          <InfoModal type="about">
            <button className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              About
            </button>
          </InfoModal>
        </div>

        {/* CTA */}
        <div className="hidden md:flex items-center gap-4">
          <SignInModal>
            <button className="text-sm text-muted-foreground hover:text-foreground transition-colors px-4 py-2">
              Sign In
            </button>
          </SignInModal>
          <SignUpModal>
            <button className="gradient-button text-sm px-5 py-2.5">
              Get Started
            </button>
          </SignUpModal>
        </div>

        {/* Mobile menu button */}
        <button
          className="md:hidden p-2 text-muted-foreground hover:text-foreground"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          <Menu className="w-6 h-6" />
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-card/95 backdrop-blur-xl border-b border-border/50 py-4 px-8">
          <div className="flex flex-col gap-4">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground">Features</a>
            <a href="#pricing" className="text-sm text-muted-foreground hover:text-foreground">Pricing</a>

            <InfoModal type="about">
              <button className="text-sm text-muted-foreground hover:text-foreground text-left w-full">
                About
              </button>
            </InfoModal>
            <hr className="border-border/50" />
            <SignInModal>
              <button className="text-sm text-muted-foreground hover:text-foreground text-left">Sign In</button>
            </SignInModal>
            <SignUpModal>
              <button className="gradient-button text-sm">Get Started</button>
            </SignUpModal>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;
