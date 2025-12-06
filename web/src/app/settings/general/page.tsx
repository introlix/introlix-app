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
          {/* User Info*/}
          <div>
            <h1 className="font-semibold">User Info</h1>
            {/* User Name */}
            <div className="flex mt-4 gap-4">
              <div className="full_name">
                <span className="text-sm text-gray-800 dark:text-gray-300">Full Name</span>
                <Input placeholder="Geoffrey Hinton" />
              </div>
              <div className="nickname">
                <span className="text-sm text-gray-800 dark:text-gray-300">Nickname</span>
                <Input placeholder="Geoffrey" />
              </div>
            </div>
            {/* User Info */}
            <div>
              <Textarea placeholder="Write a short bio about yourself..." className="w-full h-24 mt-4" />
            </div>
          </div>

          {/* Appearance setting */}
          <div className="mt-8">
            <h3 className="font-semibold">Appearance</h3>
            <div className="color_them mt-4">
              <span className="text-sm text-gray-800 dark:text-gray-300">Color Theme</span>
              <div className="cards flex gap-2">
                <div className="flex flex-col items-center">
                  <Card className={`cursor-pointer`} onClick={() => setTheme("dark")}>
                    <CardContent>
                      <MoonIcon />
                    </CardContent>
                  </Card>
                  <span>Dark</span>
                </div>
                <div className="flex flex-col items-center">
                  <Card className={`cursor-pointer`} onClick={() => setTheme("system")}>
                    <CardContent>
                      <ComputerIcon />
                    </CardContent>
                  </Card>
                  <span>System</span>
                </div>
                <div className="flex flex-col items-center">
                  <Card className={`cursor-pointer`} onClick={() => setTheme("light")}>
                    <CardContent>
                      <SunIcon />
                    </CardContent>
                  </Card>
                  <span>Light</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div >
  );
}