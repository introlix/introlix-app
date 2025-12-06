"use client";
import React from 'react';
import { Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel, SidebarMenu, SidebarMenuButton, SidebarMenuItem } from './ui/sidebar'
import Link from 'next/link';
import { usePathname } from 'next/navigation';

// Menu items.
const items = [
  {
    title: "General",
    url: "general"
  },
  {
    title: "Configuration",
    url: "configuration"
  },
]

export const SettingsSidebar = () => {
  const pathname = usePathname();
  const activeItem = items.find((item) => item.url === pathname.replace("/settings/", ""));
  return (
    <Sidebar collapsible="none" className='h-full bg-transparent'>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild className={activeItem === item ? "bg-accent" : ""}>
                    <Link href={`/settings/${item.url}`}>
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
