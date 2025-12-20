import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Info, Newspaper, Briefcase, LucideIcon } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";

interface ContentSection {
  heading: string;
  subheading?: string;
  text: string;
}

interface ModalContent {
  title: string;
  icon: LucideIcon;
  description: string;
  sections: ContentSection[];
}

interface InfoModalProps {
  children: React.ReactNode;
  type: "about" | "blog" | "careers";
}

export const InfoModal = ({ children, type }: InfoModalProps) => {
  const contentMap: Record<string, ModalContent> = {
    about: {
      title: "About AegisAI",
      icon: Info,
      description: "Our mission to protect families and businesses.",
      sections: [
        {
          heading: "Our Mission",
          text: "To create a safe viewing environment for families by filtering inappropriate language, violence, and other mature themes from movies, TV shows, and online videos. We empower parents to take control of the media their children consume."
        },
        {
          heading: "The Problem",
          text: "Manually censoring inappropriate content in video and audio is a time-consuming, costly, and inconsistent process. Parents lack effective, customizable tools to filter content for their children in real-time, often having to rely on generic ratings that don't capture specific family values."
        },
        {
          heading: "Our Solution",
          text: "AegisAI is an intelligent, privacy-focused platform that automatically detects and censors user-defined improper content. Using state-of-the-art AI, including Google Vision and OpenAI Whisper, we provide a reliable, efficient, and fully customizable solution for safe media consumption."
        }
      ]
    },
    blog: {
      title: "Latest Updates",
      icon: Newspaper,
      description: "News and announcements from the AegisAI team.",
      sections: [
        {
          heading: "Moving to Microservices & Enhanced AI Detection",
          subheading: "November 2025",
          text: "We are excited to announce a major architectural shift for AegisAI. To ensure maximum reliability and scalability, we have transitioned to a microservices architecture. This allows us to handle video processing tasks more efficiently by distributing them across specialized workers."
        },
        {
          heading: "Under the Hood",
          text: "Our new pipeline leverages the Google Vision API for unparalleled visual analysis, allowing us to detect violence and NSFW content with high precision. For audio, we are now using OpenAI's Whisper API, which provides industry-leading transcription accuracy, ensuring that even subtle profanity is caught and filtered."
        },
        {
          heading: "What's Next?",
          text: "We are currently hard at work on the 'Kids Mode' preset—a one-click solution for instant safety—and refining our real-time video player. Stay tuned for more updates as we continue to build the future of safe streaming."
        }
      ]
    },
    careers: {
      title: "Join Our Team",
      icon: Briefcase,
      description: "Help us build the future of safe media consumption.",
      sections: [
        {
          heading: "Why AegisAI?",
          text: "We are a passionate team dedicated to using AI for social good. We're solving complex technical challenges in computer vision, audio processing, and distributed systems to give families peace of mind."
        },
        {
          heading: "Open Positions",
          text: ""
        },
        {
          heading: "AI/ML Engineer",
          subheading: "Remote / Hybrid",
          text: "Work with state-of-the-art models like Google Vision and OpenAI Whisper. You will be responsible for optimizing our detection pipelines, implementing custom model training, and ensuring high precision and recall for our safety filters."
        },
        {
          heading: "Full Stack Engineer",
          subheading: "Remote / Hybrid",
          text: "Build beautiful, responsive interfaces with React/Vite and robust APIs with Python/Flask. You'll own features from end-to-end, creating the tools that parents use every day to protect their families."
        },
        {
          heading: "DevOps Engineer",
          subheading: "Remote / Hybrid",
          text: "Manage our scalable infrastructure. We use Docker, Kubernetes, RabbitMQ, and AWS. You'll ensure our microservices are performant, reliable, and secure as we scale to support more users."
        }
      ]
    }
  };

  const content = contentMap[type];
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
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {content.sections.map((section, i) => (
              <div key={i} className="mb-6 last:mb-0">
                <h3 className="text-lg font-semibold text-foreground mb-1">
                  {section.heading}
                </h3>
                {section.subheading && (
                  <p className="text-xs text-primary font-medium mb-2 uppercase tracking-wider">
                    {section.subheading}
                  </p>
                )}
                {section.text && (
                  <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                    {section.text}
                  </p>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};
