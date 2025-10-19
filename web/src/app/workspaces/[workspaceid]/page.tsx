interface ChatProps {
    params: { workspaceid: string }
}

export default async function WorkspaceDetailPage({ params }: ChatProps) {
    const { workspaceid } = await params
    return <h1>Chat ID: {workspaceid}</h1>
}