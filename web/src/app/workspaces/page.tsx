"use client";
import { Button } from '@/components/ui/button';
import { ButtonGroup } from '@/components/ui/button-group';
import { Card, CardContent, CardTitle } from '@/components/ui/card';
import { getWorkspaces } from '@/lib/api';
import { Workspace } from '@/lib/types';
import { ArrowRight, Dot, File, MessageCircle, Microscope, Plus, Search, Trash } from 'lucide-react';
import Link from 'next/link';
import React, { useEffect, useState } from 'react'
import { NewWorkspaceDialog } from '@/components/new-workspace-dialog';
import { useDeleteWorkspace } from '@/hooks/use-chat';
import { NewChatDialog } from '@/components/new-chat-dialog';

export default function WorkspacePage() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [openNewChatWindow, setOpenNewChatWindow] = useState<boolean>(false);
  const [openNewWorkspaceWindow, setOpenNewWorkspaceWindow] = useState<boolean>(false);
  const deleteWorkspace = useDeleteWorkspace();

  useEffect(() => {
    getWorkspaces().then(res => setWorkspaces(res.items));
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
  return (
    <main className="w-[80%] h-[80vh]"> {/* changed: use vh and remove overflow-y-hidden */}
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
        <div className="w-full p-4 border rounded-2xl shadow shadow-inherit overflow-y-auto max-h-[70vh] bg-card"> {/* changed: use max-h + overflow-y-auto */}
          {workspaces.length > 0 ? <div className="">
            {workspaces.map((item) => (
              <div key={item.id} className=''>
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
              </div>
            ))}
          </div> : <div className="flex justify-center items-center h-52">
            <Button onClick={() => setOpenNewWorkspaceWindow(true)} variant={'outline'} className="cursor-pointer"><Plus />New Workspace</Button>
          </div>
          }
        </div>
      </div>

      <NewWorkspaceDialog
        open={openNewWorkspaceWindow}
        onOpenChange={setOpenNewWorkspaceWindow}
        onWorkspaceCreated={async () => {
          const updated = await getWorkspaces();
          setWorkspaces(updated.items);
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
