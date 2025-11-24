import React from 'react';
import { useRouter } from 'next/navigation';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { ScrollArea } from './ui/scroll-area';
import { Button } from './ui/button';
import { Workspace } from '@/lib/types';

interface NewDeskDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    workspaces: Workspace[];
}

export const NewDeskDialog: React.FC<NewDeskDialogProps> = ({
    open,
    onOpenChange,
    workspaces
}) => {
    const router = useRouter();

    const handleWorkspaceClick = (workspaceId: string) => {
        onOpenChange(false);
        setTimeout(() => router.push(`/workspaces/${workspaceId}/desk`), 100);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm !max-w-none !w-screen !h-screen !translate-x-0 !translate-y-0 border-none shadow-none p-0">
                <div className="w-full max-w-md bg-card border rounded-2xl p-6 text-center shadow-2xl">
                    <DialogHeader className="mb-4">
                        <DialogTitle className="text-2xl font-bold">
                            Start a New Desk
                        </DialogTitle>
                        <DialogDescription className="text-sm text-muted-foreground">
                            Select a workspace to start desk in.
                        </DialogDescription>
                    </DialogHeader>

                    <ScrollArea className="max-h-[50vh] w-full space-y-2 mb-4">
                        {workspaces.length > 0 ? (
                            <div className="space-y-2 pr-4 max-h-[50vh]">
                                {workspaces.map((workspace) => (
                                    <div
                                        key={workspace.id}
                                        onClick={() => handleWorkspaceClick(workspace.id ? workspace.id : '')}
                                        className="p-4 border rounded-xl hover:bg-accent transition-colors cursor-pointer"
                                    >
                                        <div className="font-medium text-lg">{typeof workspace.name === 'string' ? workspace.name : JSON.stringify(workspace.name)}</div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-sm text-center text-muted-foreground py-6">
                                No workspaces found.
                            </div>
                        )}
                    </ScrollArea>

                    <Button
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        className="w-full cursor-pointer"
                    >
                        Cancel
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
};