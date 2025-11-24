"use client";
import React, { useEffect, useRef, useState } from 'react'
import { Button } from './ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from './ui/card';
import { ArrowRight, Check, GripVertical, Layers, Plus, X, Hash, AlertCircle, BookOpen, Trash2 } from 'lucide-react';
import { ResearchDesk } from '@/lib/types';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { cn } from '@/lib/utils';
import { useEditPlans } from '@/hooks/use-desk';

// --- Internal State Type ---
interface ResearchStep {
    id: string;
    text: string;
    priority: string;
    sources: number;
    keywords: string[];
}

const generateId = () => Math.random().toString(36).substr(2, 9);

export function useAutosizeTextArea(value: string) {
    const ref = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (!ref.current) return;
        ref.current.style.height = "auto";
        ref.current.style.height = ref.current.scrollHeight + "px";
    }, [value]);

    return ref;
}

function StepTextarea({ value, onChange, disabled }: { value: string, onChange: React.ChangeEventHandler<HTMLTextAreaElement>, disabled?: boolean }) {
    const ref = useAutosizeTextArea(value);

    return (
        <textarea
            ref={ref}
            value={value}
            onChange={onChange}
            disabled={disabled}
            rows={1}
            className={cn(
                "w-full bg-transparent border-none p-0 text-sm sm:text-base font-medium leading-relaxed resize-none focus:ring-0 focus:outline-none transition-colors",
                disabled ? "text-muted-foreground cursor-default" : "text-foreground placeholder:text-muted-foreground/50"
            )}
            placeholder="Enter research topic..."
            style={{ overflow: "hidden" }}
        />
    );
}

// Helper to colorize priority
const getPriorityColor = (p: string) => {
    switch (p.toLowerCase()) {
        case 'high': return 'text-red-600 bg-red-50 border-red-100 hover:bg-red-100';
        case 'medium': return 'text-amber-600 bg-amber-50 border-amber-100 hover:bg-amber-100';
        case 'low': return 'text-blue-600 bg-blue-50 border-blue-100 hover:bg-blue-100';
        default: return 'text-slate-600 bg-slate-50 border-slate-100 hover:bg-slate-100';
    }
};

const DeskPlanCard = ({ desk_data }: { desk_data: ResearchDesk }) => {
    const [isConfirmed, setIsConfirmed] = useState<boolean>(false);
    const editPlansMutation = useEditPlans();

    // Initialize state by mapping the nested API data to our UI state
    const [steps, setSteps] = useState<ResearchStep[]>(() => {
        if (!desk_data?.planner_agent?.topics) return [];

        return desk_data.planner_agent.topics.map(t => ({
            id: generateId(),
            text: t.topic,
            priority: t.priority.toLowerCase(),
            sources: t.estimated_sources_needed,
            keywords: t.keywords || []
        }));
    });

    // Handlers
    const handleStepChange = (id: string, field: keyof ResearchStep, value: string | number | string[]) => {
        setSteps(prev => prev.map(step => step.id === id ? { ...step, [field]: value } : step));
    };

    const addStep = () => {
        setSteps(prev => [...prev, {
            id: generateId(),
            text: "",
            priority: "medium",
            sources: 3,
            keywords: []
        }]);
    };

    const removeStep = (id: string) => {
        setSteps(prev => prev.filter(step => step.id !== id));
    };

    const handleConfirm = async () => {
        if (!desk_data.id || !desk_data.workspace_id) {
            console.error("Missing desk ID or workspace ID");
            return;
        }

        try {
            const formattedTopics = steps.map(step => ({
                topic: step.text,
                priority: step.priority,
                estimated_sources_needed: step.sources,
                keywords: step.keywords
            }));

            await editPlansMutation.mutateAsync({
                workspaceId: desk_data.workspace_id,
                deskId: desk_data.id,
                plans: formattedTopics
            });
            setIsConfirmed(true);
        } catch (error) {
            console.error("Failed to confirm plan:", error);
            // TODO: Add toast notification for error
        }
    };

    // Keyword handlers
    const addKeyword = (stepId: string, keyword: string) => {
        if (!keyword.trim()) return;
        setSteps(prev => prev.map(step => {
            if (step.id === stepId && !step.keywords.includes(keyword.trim())) {
                return { ...step, keywords: [...step.keywords, keyword.trim()] };
            }
            return step;
        }));
    };

    const removeKeyword = (stepId: string, keywordToRemove: string) => {
        setSteps(prev => prev.map(step => {
            if (step.id === stepId) {
                return { ...step, keywords: step.keywords.filter(k => k !== keywordToRemove) };
            }
            return step;
        }));
    };

    return (
        <div className="h-screen w-full p-2 sm:p-4 md:p-8 font-sans flex items-center justify-center">
            <div className="w-full max-w-4xl h-full max-h-[calc(100vh-4rem)]">

                <Card className={cn(
                    "flex flex-col h-full transition-all duration-500"
                )}>
                    <CardHeader className="flex-none pb-4 sm:pb-6 border-b border-slate-100 dark:border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 sm:gap-0 space-y-0">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-primary/10 rounded-lg">
                                <Layers className="h-5 w-5 text-primary" />
                            </div>
                            <div>
                                <CardTitle className="text-lg sm:text-xl font-semibold tracking-tight">Research Plan</CardTitle>
                                <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">Review and customize your research strategy</p>
                            </div>
                        </div>
                        <div className="text-xs font-medium text-primary bg-primary/10 px-3 py-1.5 rounded-full border border-primary/20 self-start sm:self-auto">
                            {steps.length} Steps
                        </div>
                    </CardHeader>

                    <CardContent className="flex-1 overflow-y-auto pt-4 sm:pt-6 px-3 sm:px-6 scrollbar-thin scrollbar-thumb-slate-200 dark:scrollbar-thumb-slate-800 scrollbar-track-transparent">
                        <div className="space-y-3 sm:space-y-4">
                            {steps.map((step, index) => (
                                <div
                                    key={step.id}
                                    className={cn(
                                        "group relative flex items-start gap-3 sm:gap-4 p-3 sm:p-5 rounded-xl border transition-all duration-300",
                                    )}
                                >
                                    {/* TODO: Make Drag Handle work */}
                                    {/* Drag Handle - Hidden on very small screens if needed, or kept small */}
                                    <div className={cn(
                                        "mt-1 text-slate-300 dark:text-slate-700 transition-colors hidden sm:block"
                                    )}>
                                        <GripVertical className="h-5 w-5" />
                                    </div>

                                    <div className="flex-1 space-y-3 sm:space-y-4 min-w-0">
                                        {/* Top Row: Text and Delete */}
                                        <div className="flex items-start justify-between gap-3 sm:gap-4">
                                            <div className="flex-1 min-w-0">
                                                <StepTextarea
                                                    value={step.text}
                                                    onChange={(e) => handleStepChange(step.id, 'text', e.target.value)}
                                                    disabled={isConfirmed}
                                                />
                                            </div>
                                            {!isConfirmed && (
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => removeStep(step.id)}
                                                    className="h-8 w-8 -mr-2 text-slate-400 hover:text-destructive hover:bg-destructive/10 sm:opacity-0 sm:group-hover:opacity-100 transition-all duration-200 shrink-0 cursor-pointer"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            )}
                                        </div>

                                        {/* Bottom Row: Controls */}
                                        <div className="flex flex-wrap items-center gap-2 sm:gap-3 pt-1">

                                            {/* Priority Selector */}
                                            <div className="flex items-center">
                                                {isConfirmed ? (
                                                    <div className={cn("text-[10px] uppercase tracking-wider font-semibold px-2.5 py-1 rounded-md border flex items-center gap-1.5", getPriorityColor(step.priority))}>
                                                        <AlertCircle className="h-3 w-3" />
                                                        {step.priority}
                                                    </div>
                                                ) : (
                                                    <Select
                                                        value={step.priority}
                                                        onValueChange={(val) => handleStepChange(step.id, 'priority', val)}
                                                    >
                                                        <SelectTrigger className={cn("h-7 text-[11px] uppercase tracking-wider font-semibold border-slate-200 dark:border-slate-800 cursor-pointer", getPriorityColor(step.priority))}>
                                                            <div className="flex items-center gap-1.5">
                                                                <AlertCircle className="h-3 w-3" />
                                                                <SelectValue />
                                                            </div>
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem value="high">High</SelectItem>
                                                            <SelectItem value="medium">Medium</SelectItem>
                                                            <SelectItem value="low">Low</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                )}
                                            </div>

                                            {/* Sources Input */}
                                            <div className="flex items-center gap-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-800 rounded-md px-2 py-0.5 h-7">
                                                <BookOpen className="h-3 w-3 text-slate-400" />
                                                {isConfirmed ? (
                                                    <span className="text-xs font-medium text-slate-600 dark:text-slate-300">{step.sources} Sources</span>
                                                ) : (
                                                    <div className="flex items-center gap-1">
                                                        <Input
                                                            type="number"
                                                            min={1}
                                                            max={50}
                                                            value={step.sources}
                                                            onChange={(e) => handleStepChange(step.id, 'sources', parseInt(e.target.value) || 0)}
                                                            className="h-5 w-8 p-0 text-xs border-none bg-transparent focus-visible:ring-0 text-center [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                                        />
                                                        <span className="text-xs text-muted-foreground font-medium hidden sm:inline">Sources</span>
                                                        <span className="text-xs text-muted-foreground font-medium sm:hidden">Src</span>
                                                    </div>
                                                )}
                                            </div>

                                            <div className="hidden sm:block h-4 w-[1px] bg-slate-200 dark:bg-slate-800 mx-1"></div>

                                            {/* Keywords List */}
                                            <div className="flex flex-wrap gap-2 items-center flex-1 min-w-full sm:min-w-0">
                                                {step.keywords.map((kw, i) => (
                                                    <Badge
                                                        key={i}
                                                        variant="secondary"
                                                        className="h-6 px-2 text-[10px] font-medium bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 border-transparent gap-1 transition-colors"
                                                    >
                                                        <Hash className="h-2.5 w-2.5 opacity-50" />
                                                        {kw}
                                                        {!isConfirmed && (
                                                            <button
                                                                onClick={() => removeKeyword(step.id, kw)}
                                                                className="ml-0.5 hover:text-destructive focus:outline-none cursor-pointer"
                                                            >
                                                                <X className="h-2.5 w-2.5" />
                                                            </button>
                                                        )}
                                                    </Badge>
                                                ))}

                                                {!isConfirmed && (
                                                    <div className="relative flex items-center">
                                                        <Input
                                                            placeholder="+ Tag"
                                                            className="h-6 w-16 px-1.5 text-[10px] border-dashed border-slate-300 dark:border-slate-700 bg-transparent hover:border-primary/50 focus:w-24 focus:border-primary transition-all duration-200 placeholder:text-slate-400"
                                                            onKeyDown={(e) => {
                                                                if (e.key === 'Enter') {
                                                                    addKeyword(step.id, e.currentTarget.value);
                                                                    e.currentTarget.value = '';
                                                                }
                                                            }}
                                                        />
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {!isConfirmed && (
                                <Button
                                    variant="outline"
                                    onClick={addStep}
                                    className="w-full border-dashed text-muted-foreground hover:text-primary hover:border-primary/50 hover:bg-primary/5 h-12 mt-4 transition-all duration-300 cursor-pointer"
                                >
                                    <Plus className="h-4 w-4 mr-2" /> Add Research Step
                                </Button>
                            )}
                        </div>
                    </CardContent>

                    <CardFooter className="flex-none border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 py-4 sm:py-6 px-4 sm:px-6 flex justify-end rounded-b-xl">
                        {isConfirmed ? (
                            <div className="flex items-center text-green-600 dark:text-green-500 text-sm font-medium animate-in fade-in slide-in-from-bottom-2">
                                <div className="h-8 w-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mr-3">
                                    <Check className="h-4 w-4" />
                                </div>
                                Plan Successfully Confirmed
                            </div>
                        ) : (
                            <Button
                                onClick={handleConfirm}
                                size="lg"
                                className="w-full sm:w-auto gap-2 shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all duration-300 cursor-pointer"
                            >
                                Confirm Research Plan <ArrowRight className="h-4 w-4" />
                            </Button>
                        )}
                    </CardFooter>
                </Card>

            </div>
        </div>
    );
}

export default DeskPlanCard;