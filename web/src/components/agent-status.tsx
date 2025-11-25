import { Loader2, Sparkles, Brain, Globe, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Agent status display component
 * Shows animated status indicators for different agent operations
 */
interface AgentStatusProps {
    message: string;
    subMessage?: string;
    /** Type of agent operation: loading, planning, searching, thinking, or setup */
    type?: "loading" | "planning" | "searching" | "thinking" | "setup";
}

export default function AgentStatus({ message, subMessage, type = "loading" }: AgentStatusProps) {
    const getIcon = () => {
        switch (type) {
            case "planning":
                return <Brain className="h-10 w-10 text-purple-500" />;
            case "searching":
                return <Globe className="h-10 w-10 text-blue-500" />;
            case "thinking":
                return <Sparkles className="h-10 w-10 text-amber-500" />;
            case "setup":
                return <Zap className="h-10 w-10 text-emerald-500" />;
            default:
                return <Loader2 className="h-10 w-10 text-primary animate-spin" />;
        }
    };

    const getGradient = () => {
        switch (type) {
            case "planning":
                return "from-purple-500/20 to-blue-500/20";
            case "searching":
                return "from-blue-500/20 to-cyan-500/20";
            case "thinking":
                return "from-amber-500/20 to-orange-500/20";
            case "setup":
                return "from-emerald-500/20 to-teal-500/20";
            default:
                return "from-primary/20 to-primary/10";
        }
    };

    return (
        <div className="flex flex-col items-center justify-center h-screen w-full bg-gradient-to-b from-background to-muted/20">
            <div className="flex flex-col items-center justify-center space-y-8 p-12 rounded-[2rem] bg-card/40 backdrop-blur-xl border border-white/10 shadow-2xl max-w-lg w-full mx-4 animate-fade-in-up">

                {/* Icon Container with Glow */}
                <div className="relative group">
                    <div className={cn(
                        "absolute inset-0 blur-2xl rounded-full opacity-50 transition-opacity duration-1000 group-hover:opacity-70 bg-gradient-to-r",
                        getGradient()
                    )} />
                    <div className="relative bg-background/80 p-6 rounded-2xl shadow-inner border border-white/5 ring-1 ring-white/10 backdrop-blur-md">
                        <div className={cn(
                            "transition-transform duration-700 ease-in-out",
                            type === "searching" ? "animate-pulse" : "",
                            type === "planning" ? "animate-bounce-slow" : ""
                        )}>
                            {getIcon()}
                        </div>
                    </div>
                </div>

                {/* Text Content */}
                <div className="space-y-3 text-center max-w-xs mx-auto">
                    <h2 className="text-2xl font-bold tracking-tight bg-gradient-to-br from-foreground to-foreground/60 bg-clip-text text-transparent">
                        {message}
                    </h2>
                    {subMessage && (
                        <div className="flex items-center justify-center gap-2">
                            <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                            <p className="text-muted-foreground text-sm font-medium">
                                {subMessage}
                            </p>
                        </div>
                    )}
                </div>

                {/* Progress Bar (Decorative) */}
                <div className="w-full max-w-[200px] h-1 bg-muted/50 rounded-full overflow-hidden">
                    <div className="h-full bg-primary/50 w-1/3 animate-shimmer bg-gradient-to-r from-transparent via-primary to-transparent -translate-x-full" />
                </div>
            </div>
        </div>
    );
}
