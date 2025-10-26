"use client";
import { Button } from '@/components/ui/button';
import { ButtonGroup } from '@/components/ui/button-group';
import { Card, CardContent, CardTitle } from '@/components/ui/card';
import { getWorkspaces } from '@/lib/api';
import { Workspace } from '@/lib/types';
import { Dot, File, MessageCircle, Microscope, Plus, Search, Trash } from 'lucide-react';
import Link from 'next/link';
import React, { useEffect, useState, useRef, useCallback } from 'react'
import { NewWorkspaceDialog } from '@/components/new-workspace-dialog';
import { useDeleteWorkspace } from '@/hooks/use-chat';
import { NewChatDialog } from '@/components/new-chat-dialog';

const MAX_RENDERED_ITEMS = 50; // Only keep 50 items in DOM at once

export default function WorkspacePage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [openNewChatWindow, setOpenNewChatWindow] = useState<boolean>(false);
  const [openNewWorkspaceWindow, setOpenNewWorkspaceWindow] = useState<boolean>(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const deleteWorkspace = useDeleteWorkspace();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);

  // Load initial workspaces
  useEffect(() => {
    loadWorkspaces(1, true);
  }, []);

  const loadWorkspaces = async (pageNum: number, reset: boolean = false) => {
    if (loading) return;
    
    setLoading(true);
    try {
      const res = await getWorkspaces(pageNum, 10);
      
      if (reset) {
        setWorkspaces(res.items);
      } else {
        // Add new items
        setWorkspaces(prev => {
          const newItems = [...prev, ...res.items];
          // Keep only the last MAX_RENDERED_ITEMS to prevent DOM bloat
          if (newItems.length > MAX_RENDERED_ITEMS) {
            return newItems.slice(-MAX_RENDERED_ITEMS);
          }
          return newItems;
        });
      }
      
      // Check if there are more items to load
      setHasMore(res.items.length === 10 && res.total > pageNum * 10);
      setPage(pageNum);
    } catch (error) {
      console.error("Failed to load workspaces:", error);
    } finally {
      setLoading(false);
    }
  };

  // Intersection Observer for infinite scroll
  useEffect(() => {
    if (!loadMoreRef.current || !hasMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && !loading && hasMore) {
          loadWorkspaces(page + 1);
        }
      },
      { threshold: 0.1 }
    );

    observer.observe(loadMoreRef.current);

    return () => observer.disconnect();
  }, [hasMore, loading, page]);

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

  return (
    <main className="w-[80%] h-[80vh]">
      <div className="mb-4 flex items-center justify-end">
        <ButtonGroup className="flex flex-wrap items-center gap-2">
          <Button onClick={() => setOpenNewWorkspaceWindow(true)} variant="outline" className="cursor-pointer"><Plus /> New Workspace</Button>
          <Link href={'/deep-research'}><Button variant="outline" className="cursor-pointer"><Microscope /> Deep Research</Button></Link>
          <Link href={'/research-desk'}><Button variant="outline" className="cursor-pointer"><File />Research Desk</Button></Link>
          <div><Button onClick={() => setOpenNewChatWindow(true)} variant="outline" className="cursor-pointer"><MessageCircle />Chat</Button></div>
          <Link href={'/chat?tool=search'}><Button variant="outline" className="cursor-pointer"><Search />Search</Button></Link>
        </ButtonGroup>
      </div>
      <div className="flex items-center justify-center">
        <div 
          ref={scrollContainerRef}
          className="w-full p-4 border rounded-2xl shadow shadow-inherit overflow-y-auto max-h-[70vh] bg-card"
        >
          {workspaces.length > 0 ? (
            <>
              {workspaces.map((item) => (
                <div key={item.id}>
                  <Link href={`/workspaces/${item.id}`}>
                    <Card className="bg-muted/40 hover:bg-accent transition-colors cursor-pointer mt-2">
                      <CardContent className="flex items-center justify-between">
                        <div>
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
                </div>
              ))}
              
              {/* Load more trigger */}
              <div ref={loadMoreRef} className="py-4">
                {loading && (
                  <div className="text-center text-sm text-muted-foreground">
                    Loading more workspaces...
                  </div>
                )}
                {!hasMore && !loading && (
                  <div className="text-center text-sm text-muted-foreground">
                    No more workspaces to load
                  </div>
                )}
              </div>
            </>
          ) : loading ? (
            <div className="flex justify-center items-center h-52">
              <span className="text-muted-foreground">Loading workspaces...</span>
            </div>
          ) : (
            <div className="flex justify-center items-center h-52">
              <Button onClick={() => setOpenNewWorkspaceWindow(true)} variant={'outline'} className="cursor-pointer"><Plus />New Workspace</Button>
            </div>
          )}
        </div>
      </div>

      <NewWorkspaceDialog
        open={openNewWorkspaceWindow}
        onOpenChange={setOpenNewWorkspaceWindow}
        onWorkspaceCreated={async () => {
          await loadWorkspaces(1, true);
          setPage(1);
          setHasMore(true);
        }}
      />
      <NewChatDialog
        open={openNewChatWindow}
        onOpenChange={setOpenNewChatWindow}
        workspaces={workspaces}
      />
    </main>
  )
}