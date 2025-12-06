"use client";
import { ModeToggle } from "@/components/mode-toggle";
import { SettingsSidebar } from "@/components/settings-sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { ComputerIcon, MoonIcon, SunIcon } from "lucide-react";
import { useTheme } from "next-themes";

export default function SettingsPage() {
    const { setTheme } = useTheme();
    return (
        <div className="w-[80%] h-[90%] flex flex-col">
            <h3 className="text-2xl font-bold">Settings</h3>
            <div className="flex mt-5 -ml-4 h-full">
                <SettingsSidebar />
                <div className="flex-1 pt-2 pl-5">
                    <h3 className="text-2xl font-bold">Configuration</h3>
                    {/* Model Provider */}
                    <div>
                        <h3 className="font-semibold">Model Provider</h3>
                        <div>
                            <Input placeholder="Model Provider" />
                        </div>
                    </div>
                    {/* Model */}
                    <div>
                        <h3 className="font-semibold">Model</h3>
                        <div>
                            <Input placeholder="Model" />
                        </div>
                    </div>
                </div>
            </div>
        </div >
    );
}