import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, Dot, File, MessageCircle, Microscope, Plus, Search } from "lucide-react";
import Link from "next/link";

interface ProjectData {
  id: string,
  title: string,
  url: string,
  items: number,
  updatedAt: string
}

export default function Home() {

  const projectData: ProjectData[] = [
    // { id: 'a12', title: 'Best LLM for deep research', url: '/', items: 5, updatedAt: '2 hours ago' },
    // { id: '212', title: 'Best LLM for deep research', url: '/', items: 5, updatedAt: '2 hours ago' },
    // { id: '2b2', title: 'Best LLM for deep research', url: '/', items: 5, updatedAt: '2 hours ago' },
    // { id: '215', title: 'Best LLM for deep research', url: '/', items: 5, updatedAt: '2 hours ago' },
  ]
  return (
    <main className="w-[80%] h-[80%]">
      <div className="flex items-center justify-center">
        <div className="w-full p-4 border rounded-2xl shadow shadow-inherit">
          <div className="mb-6">
            <h3 className="font-bold">Recent Workspaces</h3>
            <span className="text-accent-foreground text-sm">Your latest work</span>
          </div>
          {projectData.length > 0 ? <div className="">
            {projectData.map((item) => (
              <Link key={item.id} href={'/'}>
                <Card className="bg-card hover:bg-accent">
                  <CardContent className="">
                    <CardTitle>{item.title}</CardTitle>
                    <div className="flex text-xs text-muted-foreground items-center">
                      <span>{item.items} Items</span>
                      <Dot />
                      <span>{item.updatedAt}</span>
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
          <Link href={'/chat'}><Button variant="outline" className="cursor-pointer"><MessageCircle />Chat</Button></Link>
          <Link href={'/chat?tool=search'}><Button variant="outline" className="cursor-pointer"><Search />Search</Button></Link>
        </ButtonGroup>
      </div>
    </main>

  );
}
