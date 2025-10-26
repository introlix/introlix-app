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
import { useEffect, useState, useRef } from "react";

const MAX_RENDERED_ITEMS = 50; // Keep max 50 workspaces in memory

export default function Home() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [openNewChatWindow, setOpenNewChatWindow] = useState<boolean>(false);
  const [openNewWorkspaceWindow, setOpenNewWorkspaceWindow] = useState<boolean>(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const deleteWorkspace = useDeleteWorkspace();
  const isInitialLoad = useRef(true);

  useEffect(() => {
    loadWorkspaces(1, true);
  }, []);

  // Background loading - continues to fetch all workspaces
  useEffect(() => {
    if (!isInitialLoad.current && hasMore && !loading) {
      const timer = setTimeout(() => {
        loadWorkspaces(page + 1);
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [workspaces, hasMore, loading, page]);

  const loadWorkspaces = async (pageNum: number, reset: boolean = false) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const res = await getWorkspaces(pageNum, 10);
      
      if (reset) {
        setWorkspaces(res.items);
        isInitialLoad.current = false;
      } else {
        setWorkspaces(prev => {
          const newItems = [...prev, ...res.items];
          // Keep only the last MAX_RENDERED_ITEMS to prevent memory bloat
          if (newItems.length > MAX_RENDERED_ITEMS) {
            return newItems.slice(-MAX_RENDERED_ITEMS);
          }
          return newItems;
        });
      }
      
      // Check if there are more items to load
      const stillHasMore = res.items.length === 10 && res.total > pageNum * 10;
      setHasMore(stillHasMore);
      setPage(pageNum);
    } catch (error) {
      console.error("Failed to load workspaces:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWorkspace = async (workspaceId: string) => {
    try {
      await deleteWorkspace.mutateAsync(workspaceId);
      // Reload from the beginning after deletion
      await loadWorkspaces(1, true);
      setPage(1);
      setHasMore(true);
    } catch (error) {
      console.error("Failed to delete workspace:", error);
    }
  };

  const handleWorkspaceCreated = async () => {
    // Reload from the beginning after creation
    await loadWorkspaces(1, true);
    setPage(1);
    setHasMore(true);
  };

  // Show only top 4 workspaces on the home page
  const displayedWorkspaces = workspaces.slice(0, 4);

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
          ) : loading ? (
            <div className="flex justify-center items-center h-52">
              <span className="text-muted-foreground">Loading workspaces...</span>
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