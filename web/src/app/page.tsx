"use client";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { Card, CardContent, CardTitle } from "@/components/ui/card";
import { getWorkspaces } from "@/lib/api";
import { Workspace } from "@/lib/types";
import { ArrowRight, Dot, File, MessageCircle, Microscope, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function Home() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [openNewChatWindow, setOpenNewChatWindow] = useState<Boolean>(false);

  useEffect(() => {
    getWorkspaces().then(res => setWorkspaces(res.items));
  }, []);

  return (
    <main className="w-[80%] h-[80%]">
      <div className="flex items-center justify-center">
        <div className="w-full p-4 border rounded-2xl shadow shadow-inherit">
          <div className="mb-6">
            <h3 className="font-bold">Recent Workspaces</h3>
            <span className="text-accent-foreground text-sm">Your latest work</span>
          </div>
          {workspaces.length > 0 ? <div className="">
            {workspaces.map((item) => (
              <Link key={item.id} href={'/'}>
                <Card className="bg-card hover:bg-accent">
                  <CardContent className="">
                    <CardTitle>{item.name}</CardTitle>
                    <div className="flex text-xs text-muted-foreground items-center">
                      <span>{item.description} Items</span>
                      <Dot />
                      <span>{item.created_at}</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
            <Link href={'/workspaces'}><Button variant={'outline'} className="w-full mt-4 cursor-pointer">View All Workspaces <ArrowRight /></Button></Link>
          </div> : <div className="flex justify-center items-center h-52">
            <Button variant={'outline'} className="cursor-pointer"><Plus />New Workspace</Button>
          </div>
          }
        </div>
      </div>
      <div className="mt-4 flex items-center justify-center">
        <ButtonGroup className="flex flex-wrap items-center gap-2">
          <Link href={'/deep-research'}><Button variant="outline" className="cursor-pointer"><Microscope /> Deep Research</Button></Link>
          <Link href={'/research-desk'}><Button variant="outline" className="cursor-pointer"><File />Research Desk</Button></Link>
          <div><Button onClick={() => setOpenNewChatWindow(true)} variant="outline" className="cursor-pointer"><MessageCircle />Chat</Button></div>
          <Link href={'/chat?tool=search'}><Button variant="outline" className="cursor-pointer"><Search />Search</Button></Link>
        </ButtonGroup>
      </div>
    </main>

  );
}
