"use client";
import TextEditor from "@/components/text-editor";
import { useParams } from "next/navigation";

export default function ResearchDeskDetails() {
    const params = useParams();
    const workspaceId = params.workspaceid as string;
    const deskId = params.deskid as string;
  return (
    <main>
      <TextEditor />
    </main>
  )
}
