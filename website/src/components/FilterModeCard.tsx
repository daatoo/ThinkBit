import { ReactNode, useState } from "react";
import { ChevronDown, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import FileUploadDialog from "./FileUploadDialog";

interface FilterOption {
  label: string;
  description: string;
}

interface FilterModeCardProps {
  icon: ReactNode;
  title: string;
  description: string;
  options: FilterOption[];
  delay?: number;
  type: "audio" | "video" | "stream";
}

const FilterModeCard = ({ icon, title, description, options, delay = 0, type }: FilterModeCardProps) => {
  const [selectedOption, setSelectedOption] = useState<FilterOption | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleSelect = (option: FilterOption) => {
    setSelectedOption(option);
    setDialogOpen(true);
  };

  return (
    <>
      <div
        className={cn(
          "group relative opacity-0 animate-slide-up"
        )}
        style={{ animationDelay: `${delay}ms` }}
      >
        {/* Glow effect */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-primary/20 via-accent/20 to-primary/20 rounded-3xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        
        {/* Card */}
        <div className="relative h-full p-8 rounded-3xl bg-card/80 backdrop-blur-xl border border-border/50 group-hover:border-primary/30 transition-all duration-500 overflow-hidden">
          {/* Corner accent */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-primary/10 to-transparent rounded-bl-[100px]" />
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-accent/10 to-transparent rounded-tr-[80px]" />
          
          {/* Animated line */}
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          
          <div className="relative flex flex-col items-center text-center">
            {/* Icon with hexagon background */}
            <div className="relative mb-6">
              <div className="w-20 h-20 rotate-45 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center group-hover:scale-110 transition-transform duration-500">
                <div className="-rotate-45">
                  {icon}
                </div>
              </div>
              <Sparkles className="absolute -top-1 -right-1 w-4 h-4 text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            </div>
            
            <h3 className="text-2xl font-bold text-foreground mb-3 tracking-tight">{title}</h3>
            <p className="text-muted-foreground leading-relaxed mb-8 text-sm">{description}</p>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="relative px-6 py-3 rounded-xl font-medium text-sm transition-all duration-300 bg-secondary/80 hover:bg-secondary text-foreground border border-border/50 hover:border-primary/30 flex items-center gap-2 group/btn">
                  <span className="relative z-10">
                    {selectedOption ? selectedOption.label : "Select Mode"}
                  </span>
                  <ChevronDown className="w-4 h-4 transition-transform group-hover/btn:rotate-180 duration-300" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent 
                className="w-72 bg-card/95 backdrop-blur-xl border border-border/50 shadow-2xl shadow-primary/5 rounded-xl overflow-hidden"
                align="center"
              >
                <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
                {options.map((option, index) => (
                  <DropdownMenuItem
                    key={option.label}
                    onClick={() => handleSelect(option)}
                    className={cn(
                      "relative flex flex-col items-start gap-1 p-4 cursor-pointer transition-all duration-200",
                      "hover:bg-primary/10 focus:bg-primary/10",
                      index !== options.length - 1 && "border-b border-border/30"
                    )}
                  >
                    <span className="font-semibold text-foreground">{option.label}</span>
                    <span className="text-xs text-muted-foreground leading-relaxed">{option.description}</span>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      <FileUploadDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        filterMode={selectedOption ? { ...selectedOption, type } : null}
      />
    </>
  );
};

export default FilterModeCard;
