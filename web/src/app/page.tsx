"use client";
import { NewChatDialog } from "@/components/new-chat-dialog";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getWorkspaces } from "@/lib/api";
import { Workspace } from "@/lib/types";
import { ArrowRight, Dot, File, MessageCircle, Microscope, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Home() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [openNewChatWindow, setOpenNewChatWindow] = useState<boolean>(false);
  const router = useRouter();

  useEffect(() => {
    getWorkspaces().then((res) => setWorkspaces(res.items));
  }, []);

  return (
    <main className="w-[80%] h-[80%] mx-auto mt-6">
      {/* Recent Workspaces Section */}
      <div className="flex items-center justify-center">
        <div className="w-full p-4 border rounded-2xl shadow-sm bg-card">
          <div className="mb-6">
            <h3 className="font-bold text-lg">Recent Workspaces</h3>
            <span className="text-accent-foreground text-sm">
              Your latest work
            </span>
          </div>

          {workspaces.length > 0 ? (
            <div className="space-y-2">
              {workspaces.map((item) => (
                <Link key={item.id} href={`/workspaces/${item.id}`}>
                  <Card className="bg-muted/40 hover:bg-accent transition-colors cursor-pointer">
                    <CardContent className="py-3">
                      <CardTitle>{item.name}</CardTitle>
                      <div className="flex text-xs text-muted-foreground items-center">
                        <span>{item.description}</span>
                        <Dot />
                        <span>{item.created_at}</span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
              <Link href={"/workspaces"}>
                <Button variant="outline" className="w-full mt-4 cursor-pointer">
                  View All Workspaces <ArrowRight className="ml-1" />
                </Button>
              </Link>
            </div>
          ) : (
            <div className="flex justify-center items-center h-52">
              <Button variant="outline" className="cursor-pointer">
                <Plus className="mr-2" /> New Workspace
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Button Group Section */}
      <div className="mt-6 flex items-center justify-center">
        <ButtonGroup className="flex flex-wrap items-center gap-2">
          <Link href={"/deep-research"}>
            <Button variant="outline" className="cursor-pointer">
              <Microscope className="mr-2" /> Deep Research
            </Button>
          </Link>

          <Link href={"/research-desk"}>
            <Button variant="outline" className="cursor-pointer">
              <File className="mr-2" /> Research Desk
            </Button>
          </Link>

          <Button
            onClick={() => setOpenNewChatWindow(true)}
            variant="outline"
            className="cursor-pointer"
          >
            <MessageCircle className="mr-2" /> Chat
          </Button>

          <Link href={"/chat?tool=search"}>
            <Button variant="outline" className="cursor-pointer">
              <Search className="mr-2" /> Search
            </Button>
          </Link>
        </ButtonGroup>
      </div>
      {/* New Chat Modal */}
      <NewChatDialog open={openNewChatWindow} onOpenChange={setOpenNewChatWindow} workspaces={workspaces} />
    </main>
  );
}
