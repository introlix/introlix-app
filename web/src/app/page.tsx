"use client";
import { NewChatDialog } from "@/components/new-chat-dialog";
import { NewWorkspaceDialog } from "@/components/new-workspace-dialog";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { useDeleteWorkspace } from "@/hooks/use-chat";
import { getWorkspaces } from "@/lib/api";
import { Workspace } from "@/lib/types";
import { ArrowRight, Dot, File, MessageCircle, Microscope, Plus, Search, Trash } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function Home() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [openNewChatWindow, setOpenNewChatWindow] = useState<boolean>(false);
  const [openNewWorkspaceWindow, setOpenNewWorkspaceWindow] = useState<boolean>(false);
  const deleteWorkspace = useDeleteWorkspace();

  useEffect(() => {
    getWorkspaces().then((res) => setWorkspaces(res.items));
  }, []);

  const handleDeleteWorkspace = async (workspaceId: string) => {
    try {
      await deleteWorkspace.mutateAsync(workspaceId);
      // Refresh the workspace list after deletion
      const updatedWorkspaces = await getWorkspaces();
      setWorkspaces(updatedWorkspaces.items);
    } catch (error) {
      console.error("Failed to delete workspace:", error);
    }
  };

  const handleWorkspaceCreated = async () => {
    // Refresh the workspace list after creation
    const updatedWorkspaces = await getWorkspaces();
    setWorkspaces(updatedWorkspaces.items);
  };

  // Show only top 5 workspaces
  const displayedWorkspaces = workspaces.toReversed().slice(0, 4);

  return (
    <main className="w-[80%] h-[80%] mx-auto mt-6">
      {/* Recent Workspaces Section */}
      <div className="flex items-center justify-center">
        <div className="w-full p-4 border rounded-2xl shadow-sm bg-card">
          <div className="mb-6 flex items-center justify-between">
            <div className="">
              <h3 className="font-bold text-lg">Recent Workspaces</h3>
              <span className="text-accent-foreground text-sm">
                Your latest work
              </span>
            </div>
            <div className="flex justify-center items-center">
              <Button
                onClick={() => setOpenNewWorkspaceWindow(true)}
                variant="outline"
                size={"icon"}
                className="cursor-pointer"
              >
                <Plus className="" />
              </Button>
            </div>
          </div>

          {workspaces.length > 0 ? (
            <div className="space-y-2">
              {displayedWorkspaces.map((item) => (
                <Link key={item.id} href={`/workspaces/${item.id}`}>
                  <Card className="bg-muted/40 hover:bg-accent transition-colors cursor-pointer mt-2">
                    <CardContent className="flex items-center justify-between">
                      <div className="">
                        <CardTitle>{item.name}</CardTitle>
                        <div className="flex text-xs text-muted-foreground items-center">
                          <Dot />
                          <span>{item.created_at}</span>
                        </div>
                      </div>
                      <div
                        className="z-50"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleDeleteWorkspace(item.id ? item.id : '');
                        }}
                      >
                        <Trash className="hover:text-destructive transition-colors" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
              <Link href={"/workspaces"}>
                <Button variant="outline" className="w-full mt-2 cursor-pointer">
                  View All Workspaces <ArrowRight className="ml-1" />
                </Button>
              </Link>
            </div>
          ) : (
            <div className="flex justify-center items-center h-52">
              <Button
                onClick={() => setOpenNewWorkspaceWindow(true)}
                variant="outline"
                className="cursor-pointer"
              >
                <Plus className="mr-2" /> New Workspace
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Button Group Section */}
      <div className="mt-6 flex items-center justify-center">
        <ButtonGroup className="flex flex-wrap items-center gap-2">
          <Button
            onClick={() => setOpenNewWorkspaceWindow(true)}
            variant="outline"
            className="cursor-pointer"
          >
            <Plus className="mr-2" /> New Workspace
          </Button>

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

      {/* Modals */}
      <NewChatDialog
        open={openNewChatWindow}
        onOpenChange={setOpenNewChatWindow}
        workspaces={workspaces}
      />
      <NewWorkspaceDialog
        open={openNewWorkspaceWindow}
        onOpenChange={setOpenNewWorkspaceWindow}
        onWorkspaceCreated={handleWorkspaceCreated}
      />
    </main>
  );
}