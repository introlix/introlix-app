import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { useCreateWorkspace } from '@/hooks/use-chat';
import { Loader2 } from 'lucide-react';

interface NewWorkspaceDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onWorkspaceCreated?: () => void;
}

export const NewWorkspaceDialog: React.FC<NewWorkspaceDialogProps> = ({ 
  open, 
  onOpenChange,
  onWorkspaceCreated
}) => {
  const router = useRouter();
  const [workspaceName, setWorkspaceName] = useState('');
  const [error, setError] = useState('');
  const createWorkspace = useCreateWorkspace();

  const handleCreate = async () => {
    if (!workspaceName.trim()) {
      setError('Workspace name is required');
      return;
    }

    try {
      const newWorkspace = {
        id: null,
        name: workspaceName.trim(),
        user_id: '', // Will be set by backend
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      const newWorkspaceData = await createWorkspace.mutateAsync(newWorkspace);
      
      // Reset form
      setWorkspaceName('');
      setError('');
      
      // Notify parent component
      if (onWorkspaceCreated) {
        onWorkspaceCreated();
      }
      
      // Close dialog
      onOpenChange(false);
      
      // Navigate to new workspace
      setTimeout(() => router.push(`/workspaces/${newWorkspaceData.workspace.id}`), 100);
    } catch (err) {
      console.error('Failed to create workspace:', err);
      setError('Failed to create workspace. Please try again.');
    }
  };

  const handleCancel = () => {
    setWorkspaceName('');
    setError('');
    onOpenChange(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleCreate();
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm !max-w-none !w-screen !h-screen !translate-x-0 !translate-y-0 border-none shadow-none p-0">
        <div className="w-full max-w-md bg-card border rounded-2xl p-6 text-center shadow-2xl">
          <DialogHeader className="mb-6">
            <DialogTitle className="text-2xl font-bold">
              Create New Workspace
            </DialogTitle>
            <DialogDescription className="text-sm text-muted-foreground">
              Give your workspace a name to get started.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mb-6 text-left">
            <div className="space-y-2">
              <Label htmlFor="workspace-name">Workspace Name</Label>
              <Input
                id="workspace-name"
                placeholder="e.g., My Research Project"
                value={workspaceName}
                onChange={(e) => {
                  setWorkspaceName(e.target.value);
                  setError('');
                }}
                onKeyDown={handleKeyDown}
                disabled={createWorkspace.isPending}
                autoFocus
              />
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleCancel}
              className="flex-1 cursor-pointer"
              disabled={createWorkspace.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              className="flex-1 cursor-pointer"
              disabled={createWorkspace.isPending || !workspaceName.trim()}
            >
              {createWorkspace.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Workspace'
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};