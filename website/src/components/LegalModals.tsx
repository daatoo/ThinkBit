import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Shield, Lock, Cookie } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface LegalModalProps {
    children: React.ReactNode;
    type: "terms" | "privacy" | "cookies";
}

export const LegalModal = ({ children, type }: LegalModalProps) => {
    const content = {
        terms: {
            title: "Terms of Service",
            icon: Shield,
            description: "Please read these terms carefully before using our service.",
            text: `
          1. Acceptance of Terms
          By accessing and using this website, you accept and agree to be bound by the terms and provision of this agreement.
  
          2. Use License
          Permission is granted to temporarily download one copy of the materials (information or software) on AegisAI's website for personal, non-commercial transitory viewing only.
  
          3. Disclaimer
          The materials on AegisAI's website are provided "as is". AegisAI makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties, including without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.
  
          4. Limitations
          In no event shall AegisAI or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on AegisAI's Internet site.
  
          5. Revisions and Errata
          The materials appearing on AegisAI's web site could include technical, typographical, or photographic errors. AegisAI does not warrant that any of the materials on its web site are accurate, complete, or current.
        `
        },
        privacy: {
            title: "Privacy Policy",
            icon: Lock,
            description: "How we collect, use, and protect your data.",
            text: `
          1. Information Collection
          We collect information that you provide directly to us when you upload content for processing. We do NOT store your uploaded videos permanently. They are processed and then available for download for a limited time before being automatically deleted.
  
          2. Use of Information
          The uploaded content is used solely for the purpose of the requested processing (filtering/safety checks). We do not use your content for training public AI models without your explicit consent.
  
          3. Data Security
          We implement a variety of security measures to maintain the safety of your personal information. Your files are stored in secure, private environments.
  
          4. Cookies
          We use cookies to understand and save your preferences for future visits and compile aggregate data about site traffic and site interaction.
        `
        },
        cookies: {
            title: "Cookie Policy",
            icon: Cookie,
            description: "Understanding how we use cookies.",
            text: `
          1. What are cookies?
          Cookies are small files that a site or its service provider transfers to your computers hard drive through your Web browser (if you allow) that enables the sites or service providers systems to recognize your browser and capture and remember certain information.
  
          2. How we use cookies
          We use cookies to help us remember and process the items in your shopping cart, understand and save your preferences for future visits and keep track of advertisements.
  
          3. Managing cookies
          You can choose to have your computer warn you each time a cookie is being sent, or you can choose to turn off all cookies. You do this through your browser settings.
        `
        }
    }[type];

    const Icon = content.icon;

    return (
        <Dialog>
            <DialogTrigger asChild>
                {children}
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px] bg-background/95 backdrop-blur-xl border-border/50">
                <DialogHeader>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
                            <Icon className="w-5 h-5 text-primary" />
                        </div>
                        <DialogTitle className="text-2xl">{content.title}</DialogTitle>
                    </div>
                    <DialogDescription>
                        {content.description}
                    </DialogDescription>
                </DialogHeader>
                <ScrollArea className="h-[400px] w-full rounded-md border border-border/50 p-4 mt-4 bg-muted/20">
                    <div className="prose prose-sm dark:prose-invert">
                        {content.text.split('\n\n').map((paragraph, i) => (
                            <p key={i} className="mb-4 text-muted-foreground leading-relaxed whitespace-pre-line">
                                {paragraph.trim()}
                            </p>
                        ))}
                    </div>
                </ScrollArea>
            </DialogContent>
        </Dialog>
    );
};
