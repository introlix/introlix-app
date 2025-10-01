import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuSub,
    SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@radix-ui/react-collapsible";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@radix-ui/react-dropdown-menu";
import { ChevronDown, Folder, Plus, Search, Sparkles, SquarePen } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { Input } from "./ui/input";

// Menu items.
const items = [
    {
        title: "New Research",
        url: '/',
        icon: SquarePen,
    },
    {
        title: "Search Project/Researches",
        url: '/',
        icon: Search,
    }
]

// Projects Item
const projects = [
    {
        title: "Project1",
        items: [
            {
                title: 'Research 1',
                url: '/'
            },
            {
                title: 'Research 2',
                url: '/'
            },
            {
                title: 'Research 3',
                url: '/'
            },
            {
                title: 'Research 4',
                url: '/'
            }
        ]
    },
    {
        title: "Project2",
        items: [
            {
                title: 'Research 1',
                url: '/'
            },
            {
                title: 'Research 2',
                url: '/'
            },
            {
                title: 'Research 3',
                url: '/'
            },
            {
                title: 'Research 4',
                url: '/'
            }
        ]
    },
    {
        title: "Project3",
        items: [
            {
                title: 'Research 1',
                url: '/'
            },
            {
                title: 'Research 2',
                url: '/'
            },
            {
                title: 'Research 3',
                url: '/'
            },
            {
                title: 'Research 4',
                url: '/'
            }
        ]
    },
    {
        title: "Project4",
        items: [
            {
                title: 'Research 1',
                url: '/'
            },
            {
                title: 'Research 2',
                url: '/'
            },
            {
                title: 'Research 3',
                url: '/'
            },
            {
                title: 'Research 4',
                url: '/'
            }
        ]
    },
    {
        title: "Project5",
        items: [
            {
                title: 'Research 1',
                url: '/'
            },
            {
                title: 'Research 2',
                url: '/'
            },
            {
                title: 'Research 3',
                url: '/'
            },
            {
                title: 'Research 4',
                url: '/'
            }
        ]
    }
]

export function AppSidebar() {
    return (
        <Sidebar>
            <SidebarHeader>
                <Collapsible className="group/collapsible">
                    <SidebarGroup>
                        <SidebarGroupLabel asChild>
                            <CollapsibleTrigger className="cursor-pointer">
                                <Image src={'./vercel.svg'} alt="Logo" width={20} height={20} />
                                <h3 className="text-xl ml-auto">Introlix</h3>
                                <ChevronDown className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-180" />
                            </CollapsibleTrigger>
                        </SidebarGroupLabel>
                        <CollapsibleContent>
                            <SidebarGroupContent>
                                <SidebarMenu>
                                    <SidebarMenuItem className="border border-secondary rounded-xl mt-3">
                                        <SidebarMenuButton asChild>
                                            <Link href={'/subscription'}>
                                                <Sparkles />Introlix Pro
                                            </Link>
                                        </SidebarMenuButton>
                                        <SidebarMenuButton asChild>
                                            <Link href={'/subscription'}>
                                                <Plus />Introlix Basic
                                            </Link>
                                        </SidebarMenuButton>
                                    </SidebarMenuItem>
                                </SidebarMenu>
                            </SidebarGroupContent>
                        </CollapsibleContent>
                    </SidebarGroup>
                </Collapsible>
            </SidebarHeader>
            <SidebarContent>
                <SidebarGroup>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {items.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton asChild>
                                        <Link href={item.url}>
                                            <item.icon />
                                            <span>{item.title}</span>
                                        </Link>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                    <SidebarGroupContent className="mt-5">
                        <SidebarGroupLabel>Projects</SidebarGroupLabel>
                        <SidebarMenu>
                            {projects.map((project) => (
                                <SidebarMenuItem key={project.title}>
                                    <Collapsible defaultOpen={false} className="group/collapsible">
                                        <CollapsibleTrigger asChild>
                                            <SidebarMenuButton>
                                                {project.title}
                                                <ChevronDown className="ml-auto transition-transform group-data-[state=open]/collapsible:rotate-180" />
                                            </SidebarMenuButton>
                                        </CollapsibleTrigger>

                                        <CollapsibleContent>
                                            <SidebarMenuSub>
                                                {project.items.map((research) => (
                                                    <SidebarMenuSubItem key={research.title}>
                                                        <Link href={research.url}>{research.title}</Link>
                                                    </SidebarMenuSubItem>
                                                ))}
                                            </SidebarMenuSub>
                                        </CollapsibleContent>
                                    </Collapsible>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>

                    </SidebarGroupContent>
                </SidebarGroup>
                <SidebarGroup />
            </SidebarContent>
            <SidebarFooter />
        </Sidebar>
    )
}