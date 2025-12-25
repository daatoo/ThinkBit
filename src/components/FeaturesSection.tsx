import { FileAudio, Video, Radio } from "lucide-react";
import FilterModeCard from "./FilterModeCard";

const FeaturesSection = () => {
  const features = [
    {
      icon: <FileAudio className="w-10 h-10 text-primary" />,
      title: "Audio",
      description: "Filter podcasts, audiobooks, and music. Our AI detects profanity and inappropriate content seamlessly.",
      delay: 100,
      type: "audio" as const,
      options: [
        {
          label: "Audio File → Clean Audio",
          description: "Upload audio files and receive filtered versions",
        },
        {
          label: "Audio Stream → Clean Stream",
          description: "Real-time audio filtering for live broadcasts",
        },
      ],
    },
    {
      icon: <Video className="w-10 h-10 text-primary" />,
      title: "Video File",
      description: "Upload videos and let AI automatically detect and filter inappropriate visual and audio content.",
      delay: 200,
      type: "video" as const,
      options: [
        {
          label: "Clean Audio Only",
          description: "Filter audio track, keep video unchanged",
        },
        {
          label: "Clean Video Only",
          description: "Blur visual content, keep audio unchanged",
        },
        {
          label: "Full Filter",
          description: "Filter both video and audio completely",
        },
      ],
    },
    {
      icon: <Radio className="w-10 h-10 text-primary" />,
      title: "Live Stream",
      description: "Real-time content moderation for live broadcasts. Perfect for TV stations requiring instant filtering.",
      delay: 300,
      type: "stream" as const,
      options: [
        {
          label: "Clean Audio Only",
          description: "Filter audio stream, keep video unchanged",
        },
        {
          label: "Clean Video Only",
          description: "Blur visual content in real-time",
        },
        {
          label: "Full Filter",
          description: "Filter both video and audio live",
        },
      ],
    },
  ];

  return (
    <section id="features" className="relative py-24 px-8">
      {/* Background accent */}
      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-px h-64 bg-gradient-to-b from-transparent via-primary/30 to-transparent" />
      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-px h-64 bg-gradient-to-b from-transparent via-primary/30 to-transparent" />

      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-20">
          <span 
            className="inline-block text-sm font-mono text-primary mb-4 tracking-widest uppercase opacity-0 animate-fade-in"
          >
            Filtering Modes
          </span>
          <h2 
            className="text-4xl md:text-5xl font-bold text-foreground mb-6 opacity-0 animate-fade-in"
            style={{ animationDelay: "50ms" }}
          >
            Choose Your Shield
          </h2>
          <p 
            className="text-muted-foreground text-lg max-w-xl mx-auto opacity-0 animate-fade-in"
            style={{ animationDelay: "100ms" }}
          >
            Select content type and filtering mode. Our AI adapts to provide optimal protection.
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature) => (
            <FilterModeCard
              key={feature.title}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              options={feature.options}
              delay={feature.delay}
              type={feature.type}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;
