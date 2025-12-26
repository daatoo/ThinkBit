import { Menu, LogOut, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { InfoModal } from "./InfoModals";
import { SignInModal, SignUpModal } from "./AuthModals";
import { useAuth } from "@/hooks/use-auth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const Header = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full">
      {/* Blur backdrop */}
      <div className="absolute inset-0 bg-background/80 backdrop-blur-xl border-b border-border/50" />

      <nav className="relative max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center gap-3 group">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/25 shadow-inner group-hover:shadow-primary/40 transition-shadow">
            <img src="/logo.png" alt="AegisAI Logo" className="w-8 h-8 object-contain drop-shadow-[0_0_2px_rgba(255,255,255,0.9)]" />
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

        {/* CTA / User Menu */}
        <div className="hidden md:flex items-center gap-4">
          {isAuthenticated && user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-background/50 transition-colors">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-primary/20 text-primary text-xs font-semibold">
                      {user.email.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-sm text-foreground font-medium max-w-[150px] truncate">
                    {user.email}
                  </span>
                  <CheckCircle2 className="w-4 h-4 text-primary" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{user.email}</p>
                    <p className="text-xs text-muted-foreground">Signed in</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-red-500 cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <>
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
            </>
          )}
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
      {
        mobileMenuOpen && (
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
              {isAuthenticated && user ? (
                <>
                  <div className="flex items-center gap-2 px-2 py-2">
                    <Avatar className="w-8 h-8">
                      <AvatarFallback className="bg-primary/20 text-primary text-xs font-semibold">
                        {user.email.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-foreground">{user.email}</span>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-primary" />
                        Signed in
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={logout}
                    className="text-sm text-red-500 hover:text-red-600 text-left flex items-center gap-2 px-2 py-2"
                  >
                    <LogOut className="w-4 h-4" />
                    Log out
                  </button>
                </>
              ) : (
                <>
                  <SignInModal>
                    <button className="text-sm text-muted-foreground hover:text-foreground text-left">Sign In</button>
                  </SignInModal>
                  <SignUpModal>
                    <button className="gradient-button text-sm">Get Started</button>
                  </SignUpModal>
                </>
              )}
            </div>
          </div>
        )
      }
    </header >
  );
};

export default Header;
