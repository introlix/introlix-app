"use client";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { Dot, File, MessageCircle, Microscope, Search } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

const MAX_RENDERED_ITEMS = 50;

// Replace this with your actual API call
// Check your lib/api.ts file for the correct function
async function getWorkspaceItems(workspaceId: string, page: number, limit: number) {
    // OPTION 1: If you have a function in lib/api.ts, import and use it
    // import { getWorkspaceItems } from '@/lib/api';
    
    // OPTION 2: Use the correct API endpoint
    const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const res = await fetch(`${BASE_URL}/workspaces/${workspaceId}/items?page=${page}&limit=${limit}`);
    if (!res.ok) {
        throw new Error('Failed to fetch workspace items');
    }
    return res.json();
}

export default function WorkspaceDetailPage() {
    const [workspaceItems, setWorkspaceItems] = useState<any[]>([]);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [loading, setLoading] = useState(false);
    
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const loadMoreRef = useRef<HTMLDivElement>(null);
    const params = useParams();
    const workspaceId = params.workspaceid as string;

    // Load initial workspace items
    useEffect(() => {
        loadWorkspaceItems(1, true);
    }, [workspaceId]);

    const loadWorkspaceItems = async (pageNum: number, reset: boolean = false) => {
        if (loading) return;
        
        setLoading(true);
        try {
            const res = await getWorkspaceItems(workspaceId, pageNum, 10);
            
            if (reset) {
                setWorkspaceItems(res.items || []);
            } else {
                // Add new items
                setWorkspaceItems(prev => {
                    const newItems = [...prev, ...(res.items || [])];
                    // Keep only the last MAX_RENDERED_ITEMS to prevent DOM bloat
                    if (newItems.length > MAX_RENDERED_ITEMS) {
                        return newItems.slice(-MAX_RENDERED_ITEMS);
                    }
                    return newItems;
                });
            }
            
            // Check if there are more items to load
            const itemsLength = res.items?.length || 0;
            const total = res.total || 0;
            setHasMore(itemsLength === 10 && total > pageNum * 10);
            setPage(pageNum);
        } catch (error) {
            console.error("Failed to load workspace items:", error);
            setWorkspaceItems([]);
            setHasMore(false);
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
                    loadWorkspaceItems(page + 1);
                }
            },
            { threshold: 0.1 }
        );

        observer.observe(loadMoreRef.current);

        return () => observer.disconnect();
    }, [hasMore, loading, page]);

    return (
        <main className="w-[80%] h-[80vh]">
            <div className="mb-4 flex items-center justify-end">
                <ButtonGroup className="flex flex-wrap items-center gap-2">
                    <Link href={'/deep-research'}>
                        <Button variant="outline" className="cursor-pointer">
                            <Microscope /> Deep Research
                        </Button>
                    </Link>
                    <Link href={'/research-desk'}>
                        <Button variant="outline" className="cursor-pointer">
                            <File />Research Desk
                        </Button>
                    </Link>
                    <Link href={`/workspaces/${workspaceId}/chat`}>
                        <Button 
                            variant="outline" 
                            className="cursor-pointer"
                        >
                            <MessageCircle />Chat
                        </Button>
                    </Link>
                    <Link href={'/chat?tool=search'}>
                        <Button variant="outline" className="cursor-pointer">
                            <Search />Search
                        </Button>
                    </Link>
                </ButtonGroup>
            </div>
            <div className="flex items-center justify-center">
                <div 
                    ref={scrollContainerRef}
                    className="w-full p-4 border rounded-2xl shadow shadow-inherit overflow-y-auto max-h-[70vh] bg-card"
                >
                    {workspaceItems.length > 0 ? (
                        <>
                            {workspaceItems.map((item) => (
                                <div key={item.id}>
                                    <Link href={`/workspaces/${item.workspace_id}/chat/${item.id}`}>
                                        <Card className="bg-muted/40 hover:bg-accent transition-colors cursor-pointer mt-2">
                                            <CardContent className="flex items-center justify-between">
                                                <div>
                                                    <CardTitle>{item.title}</CardTitle>
                                                    <div className="flex text-xs text-muted-foreground items-center">
                                                        <Dot />
                                                        <span>{item.created_at}</span>
                                                    </div>
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
                                        Loading more items...
                                    </div>
                                )}
                                {!hasMore && !loading && (
                                    <div className="text-center text-sm text-muted-foreground">
                                        No more items to load
                                    </div>
                                )}
                            </div>
                        </>
                    ) : loading ? (
                        <div className="flex justify-center items-center h-52">
                            <span className="text-muted-foreground">Loading items...</span>
                        </div>
                    ) : (
                        <div className="flex justify-center items-center h-52">
                            <span className="text-muted-foreground">No Items In Workspace</span>
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}