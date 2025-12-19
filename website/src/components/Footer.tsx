import { Shield } from "lucide-react";
import { LegalModal } from "./LegalModals";

const Footer = () => {
  return (
    <footer className="relative py-16 px-8 border-t border-border/30 bg-background/50 backdrop-blur-lg">
      <div className="max-w-6xl mx-auto">
        <div className="grid md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="md:col-span-1">
            <a href="/" className="flex items-center gap-3 mb-4 group">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center transform group-hover:scale-110 transition-transform duration-300">
                <Shield className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold gradient-text">AegisAI</span>
            </a>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Protecting families and businesses with intelligent, privacy-focused content filtering.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-semibold text-foreground mb-4 text-sm uppercase tracking-wider">Product</h4>
            <ul className="space-y-3">
              <li><a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">Features</a></li>
              <li><a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">Pricing</a></li>
              <li><a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">API</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-foreground mb-4 text-sm uppercase tracking-wider">Company</h4>
            <ul className="space-y-3">
              <li><a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">About</a></li>
              <li><a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">Blog</a></li>
              <li><a href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors">Careers</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-foreground mb-4 text-sm uppercase tracking-wider">Legal</h4>
            <ul className="space-y-3">
              <li>
                <LegalModal type="privacy">
                  <button className="text-sm text-muted-foreground hover:text-primary transition-colors text-left">
                    Privacy Policy
                  </button>
                </LegalModal>
              </li>
              <li>
                <LegalModal type="terms">
                  <button className="text-sm text-muted-foreground hover:text-primary transition-colors text-left">
                    Terms of Service
                  </button>
                </LegalModal>
              </li>
              <li>
                <LegalModal type="cookies">
                  <button className="text-sm text-muted-foreground hover:text-primary transition-colors text-left">
                    Cookie Policy
                  </button>
                </LegalModal>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="pt-8 border-t border-border/30 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} AegisAI. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors text-sm">Twitter</a>
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors text-sm">GitHub</a>
            <a href="#" className="text-muted-foreground hover:text-primary transition-colors text-sm">Discord</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
