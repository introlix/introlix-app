'use client';

import React, { useCallback, useEffect, useState, useRef } from 'react';
import debounce from 'lodash.debounce';
import type { ReactNode } from 'react';
import { LexicalComposer } from '@lexical/react/LexicalComposer';
import type { InitialConfigType } from '@lexical/react/LexicalComposer';
import { RichTextPlugin } from '@lexical/react/LexicalRichTextPlugin';
import { ContentEditable } from '@lexical/react/LexicalContentEditable';
import { HistoryPlugin } from '@lexical/react/LexicalHistoryPlugin';
import { AutoFocusPlugin } from '@lexical/react/LexicalAutoFocusPlugin';
import { OnChangePlugin } from '@lexical/react/LexicalOnChangePlugin';
import { useLexicalComposerContext } from '@lexical/react/LexicalComposerContext';
import {
    HeadingNode,
    QuoteNode,
    $createHeadingNode,
    $createQuoteNode,
} from '@lexical/rich-text';
import type { HeadingTagType } from '@lexical/rich-text';
import { TableCellNode, TableNode, TableRowNode } from '@lexical/table';
import { ListItemNode, ListNode } from '@lexical/list';
import { CodeHighlightNode, CodeNode } from '@lexical/code';
import { AutoLinkNode, LinkNode } from '@lexical/link';
import { LinkPlugin } from '@lexical/react/LexicalLinkPlugin';
import { ListPlugin } from '@lexical/react/LexicalListPlugin';
import { MarkdownShortcutPlugin } from '@lexical/react/LexicalMarkdownShortcutPlugin';
import { TRANSFORMERS, $convertToMarkdownString, $convertFromMarkdownString } from '@lexical/markdown';
import {
    $getSelection,
    $isRangeSelection,
    FORMAT_TEXT_COMMAND,
    UNDO_COMMAND,
    REDO_COMMAND,
    FORMAT_ELEMENT_COMMAND,
    $createParagraphNode,
    $getRoot,
    $createTextNode,
    LexicalEditor
} from 'lexical';
import type {
    EditorState,
    ElementFormatType,
    TextFormatType,
} from 'lexical';
import {
    INSERT_ORDERED_LIST_COMMAND,
    INSERT_UNORDERED_LIST_COMMAND,
} from '@lexical/list';
import {
    Bold,
    Italic,
    Underline,
    Strikethrough,
    AlignLeft,
    AlignCenter,
    AlignRight,
    List,
    ListOrdered,
    Heading1,
    Heading2,
    Heading3,
    Heading4,
    Heading5,
    Heading6,
    Quote,
    Undo2,
    Redo2,
    Download,
    FileText,
    X,
} from 'lucide-react';
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from './ui/select';
import { useDesk, useAddDocumentToDesk } from '@/hooks/use-desk';
import { Message } from '@/lib/types';

// --- EXPORT DIALOG ---
interface ExportDialogProps {
    onClose: () => void;
}

function ExportDialog({ onClose }: ExportDialogProps) {
    const [editor] = useLexicalComposerContext();

    const formats = [
        { key: 'md', label: 'Markdown (.md)', style: 'Preserves headings, lists, and basic formatting.' },
        { key: 'txt', label: 'Plain Text (.txt)', style: 'Content only, no style preserved.' },
    ];

    const handleSelectFormat = (formatKey: string) => {
        editor.read(() => {
            const content = formatKey === 'md'
                ? $convertToMarkdownString(TRANSFORMERS)
                : $getRoot().getTextContent();

            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `document.${formatKey}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
        onClose();
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-card rounded-lg shadow-2xl w-full max-w-lg p-6 border border-border">
                <div className="flex justify-between items-start mb-4 border-b pb-2">
                    <h3 className="text-xl font-semibold">Export Document Format</h3>
                    <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
                        <X className="h-5 w-5" />
                    </button>
                </div>
                <div className="space-y-3">
                    {formats.map((f) => (
                        <button
                            key={f.key}
                            onClick={() => handleSelectFormat(f.key)}
                            className="w-full text-left p-3 rounded-md border border-input hover:bg-accent/60 transition-colors bg-accent/20"
                        >
                            <p className="font-medium text-lg">{f.label}</p>
                            <p className="text-sm text-muted-foreground">{f.style}</p>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

// --- TOOLBAR PLUGIN ---
interface ToolbarButtonProps {
    onClick: React.MouseEventHandler<HTMLButtonElement>;
    active?: boolean;
    title: string;
    children: ReactNode;
}

function ToolbarPlugin({ openExportDialog }: { openExportDialog: () => void }) {
    const [heading, setHeading] = useState("normal");
    const [editor] = useLexicalComposerContext();
    const [activeStates, setActiveStates] = useState({
        bold: false,
        italic: false,
        underline: false,
        strikethrough: false,
    });

    useEffect(() => {
        return editor.registerUpdateListener(({ editorState }) => {
            editorState.read(() => {
                const selection = $getSelection();
                if ($isRangeSelection(selection)) {
                    setActiveStates({
                        bold: selection.hasFormat('bold'),
                        italic: selection.hasFormat('italic'),
                        underline: selection.hasFormat('underline'),
                        strikethrough: selection.hasFormat('strikethrough'),
                    });
                }
            });
        });
    }, [editor]);

    const handleChange = (value: string) => {
        setHeading(value);
        editor.update(() => {
            const selection = $getSelection();
            if ($isRangeSelection(selection)) {
                if (value === "normal") {
                    selection.insertNodes([$createParagraphNode()]);
                } else {
                    const allowed: Array<string> = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'];
                    if (allowed.includes(value)) {
                        selection.insertNodes([$createHeadingNode(value as HeadingTagType)]);
                    }
                }
            }
        });
    };

    const formatText = (format: TextFormatType) => {
        editor.dispatchCommand(FORMAT_TEXT_COMMAND, format);
    };

    const formatAlign = (alignment: ElementFormatType) => {
        editor.dispatchCommand(FORMAT_ELEMENT_COMMAND, alignment);
    };

    const formatQuote = () => {
        editor.update(() => {
            const selection = $getSelection();
            if ($isRangeSelection(selection)) {
                selection.insertNodes([$createQuoteNode()]);
            }
        });
    };

    const ToolbarButton = ({ onClick, active, title, children }: ToolbarButtonProps) => (
        <button
            onClick={onClick}
            type="button"
            title={title}
            className={`inline-flex items-center justify-center h-8 px-2.5 rounded text-sm font-medium transition-colors ${active ? 'bg-accent text-accent-foreground' : 'hover:bg-accent/50 text-muted-foreground hover:text-foreground'
                }`}
        >
            {children}
        </button>
    );

    const ToolbarDivider = () => <div className="w-px h-5 bg-border mx-1" />;

    return (
        <div className="border-b bg-background/95 backdrop-blur sticky top-0 z-50">
            <div className="flex items-center gap-1 px-4 py-2">
                <div className="flex items-center gap-1">
                    <ToolbarButton onClick={() => editor.dispatchCommand(UNDO_COMMAND, undefined)} title="Undo">
                        <Undo2 className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                    <ToolbarButton onClick={() => editor.dispatchCommand(REDO_COMMAND, undefined)} title="Redo">
                        <Redo2 className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                </div>

                <ToolbarDivider />

                <Select value={heading} onValueChange={handleChange}>
                    <SelectTrigger className="w-[180px] cursor-pointer">
                        <SelectValue placeholder="Normal" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectGroup>
                            <SelectLabel>Headings</SelectLabel>
                            <SelectItem className='cursor-pointer' value="normal">
                                <FileText className="h-4 w-4 mr-2 inline" /> Normal
                            </SelectItem>
                            <SelectItem className='cursor-pointer' value="h1">
                                <Heading1 className="h-4 w-4 mr-2 inline" /> Heading 1
                            </SelectItem>
                            <SelectItem className='cursor-pointer' value="h2">
                                <Heading2 className="h-4 w-4 mr-2 inline" /> Heading 2
                            </SelectItem>
                            <SelectItem className='cursor-pointer' value="h3">
                                <Heading3 className="h-4 w-4 mr-2 inline" /> Heading 3
                            </SelectItem>
                            <SelectItem className='cursor-pointer' value="h4">
                                <Heading4 className="h-4 w-4 mr-2 inline" /> Heading 4
                            </SelectItem>
                            <SelectItem className='cursor-pointer' value="h5">
                                <Heading5 className="h-4 w-4 mr-2 inline" /> Heading 5
                            </SelectItem>
                            <SelectItem className='cursor-pointer' value="h6">
                                <Heading6 className="h-4 w-4 mr-2 inline" /> Heading 6
                            </SelectItem>
                        </SelectGroup>
                    </SelectContent>
                </Select>

                <ToolbarDivider />

                <div className="flex items-center gap-1">
                    <ToolbarButton onClick={() => formatText('bold')} active={activeStates.bold} title="Bold">
                        <Bold className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                    <ToolbarButton onClick={() => formatText('italic')} active={activeStates.italic} title="Italic">
                        <Italic className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                    <ToolbarButton onClick={() => formatText('underline')} active={activeStates.underline} title="Underline">
                        <Underline className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                    <ToolbarButton onClick={() => formatText('strikethrough')} active={activeStates.strikethrough} title="Strikethrough">
                        <Strikethrough className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                </div>

                <ToolbarDivider />

                <div className="flex items-center gap-1">
                    <ToolbarButton onClick={() => formatAlign('left')} title="Align Left">
                        <AlignLeft className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                    <ToolbarButton onClick={() => formatAlign('center')} title="Align Center">
                        <AlignCenter className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                    <ToolbarButton onClick={() => formatAlign('right')} title="Align Right">
                        <AlignRight className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                </div>

                <ToolbarDivider />

                <div className="flex items-center gap-1">
                    <ToolbarButton onClick={() => editor.dispatchCommand(INSERT_UNORDERED_LIST_COMMAND, undefined)} title="Bullet List">
                        <List className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                    <ToolbarButton onClick={() => editor.dispatchCommand(INSERT_ORDERED_LIST_COMMAND, undefined)} title="Numbered List">
                        <ListOrdered className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                    <ToolbarButton onClick={formatQuote} title="Quote">
                        <Quote className="h-4 w-4 cursor-pointer" />
                    </ToolbarButton>
                </div>

                <div className="flex-1" />

                <div className="flex items-center gap-2">
                    <button
                        onClick={openExportDialog}
                        title="Export Document"
                        className="inline-flex items-center justify-center h-8 px-3 rounded border border-input hover:bg-accent hover:text-accent-foreground text-sm"
                    >
                        <Download className="h-4 w-4 mr-1.5" />
                        <span>Export</span>
                    </button>
                </div>
            </div>
        </div>
    );
}

// --- LOAD CONTENT PLUGIN ---
function LoadContentPlugin({ content, deskId, messages }: { content?: string; deskId: string; messages: Message[] }) {
    const [editor] = useLexicalComposerContext();
    const loadedDeskRef = useRef<string | null>(null);
    const hasLoadedRef = useRef(false);
    const lastMessageIdRef = useRef<string | null>(null);

    useEffect(() => {
        // Reset when desk changes
        if (loadedDeskRef.current !== deskId) {
            hasLoadedRef.current = false;
            loadedDeskRef.current = deskId;
            lastMessageIdRef.current = null;
        }
    }, [deskId]);

    useEffect(() => {
        // Only load once per desk and only if we have content
        if (!content || hasLoadedRef.current) return;

        editor.update(() => {
            const root = $getRoot();
            root.clear();

            try {
                $convertFromMarkdownString(content, TRANSFORMERS);
            } catch (err) {
                console.error('Failed to load markdown:', err);
            }
        });

        hasLoadedRef.current = true;
        // Initialize last message id
        if (messages && messages.length > 0) {
            lastMessageIdRef.current = messages[messages.length - 1].id;
        }
    }, [editor, content, messages]);

    // Handle updates from Assistant
    useEffect(() => {
        if (!content || !hasLoadedRef.current) return;

        const lastMsg = messages && messages.length > 0 ? messages[messages.length - 1] : null;

        if (!lastMsg) return;
        if (lastMsg.id === lastMessageIdRef.current) return;

        lastMessageIdRef.current = lastMsg.id;

        if (lastMsg.role === 'assistant') {
            editor.read(() => {
                const currentMarkdown = $convertToMarkdownString(TRANSFORMERS);
                if (currentMarkdown !== content) {
                    editor.update(() => {
                        const root = $getRoot();
                        root.clear();
                        try {
                            $convertFromMarkdownString(content, TRANSFORMERS);
                        } catch (err) {
                            console.error('Failed to load markdown:', err);
                        }
                    });
                }
            });
        }
    }, [messages, content, editor]);

    return null;
}

// --- THEME ---
const theme = {
    paragraph: 'mb-3 leading-relaxed',
    heading: {
        h1: 'text-4xl font-bold mb-4 mt-8 leading-tight',
        h2: 'text-3xl font-semibold mb-3 mt-6 leading-tight',
        h3: 'text-2xl font-semibold mb-2 mt-5 leading-snug',
    },
    list: {
        ul: 'list-disc ml-5 mb-3 space-y-1',
        ol: 'list-decimal ml-5 mb-3 space-y-1',
        listitem: 'ml-0',
    },
    text: {
        bold: 'font-semibold',
        italic: 'italic',
        underline: 'underline underline-offset-2',
        strikethrough: 'line-through',
    },
    quote: 'border-l-4 border-primary/40 pl-4 py-2 my-4 italic text-muted-foreground bg-muted/30',
    code: 'bg-muted px-1.5 py-0.5 rounded-sm font-mono text-sm',
};

function onError(error: Error) {
    console.error(error);
}

export default function TextEditor({ workspaceId, deskId }: { workspaceId: string; deskId: string }) {
    const addDocument = useAddDocumentToDesk();
    const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
    const isInitialLoadRef = useRef(true);
    const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const initialConfig: InitialConfigType = {
        namespace: 'ResearchDeskEditor',
        theme,
        onError,
        nodes: [
            HeadingNode,
            ListNode,
            ListItemNode,
            QuoteNode,
            CodeNode,
            CodeHighlightNode,
            TableNode,
            TableCellNode,
            TableRowNode,
            AutoLinkNode,
            LinkNode,
        ],
    };

    // Reset initial load flag when desk changes
    useEffect(() => {
        isInitialLoadRef.current = true;
        const timer = setTimeout(() => {
            isInitialLoadRef.current = false;
        }, 2000); // Wait 2 seconds before enabling autosave
        return () => clearTimeout(timer);
    }, [deskId]);

    const onChange = useCallback((editorState: EditorState) => {
        // Skip saving during initial load period
        if (isInitialLoadRef.current) return;

        // Clear existing timeout
        if (saveTimeoutRef.current) {
            clearTimeout(saveTimeoutRef.current);
        }

        // Debounce the save
        saveTimeoutRef.current = setTimeout(() => {
            editorState.read(() => {
                const markdown = $convertToMarkdownString(TRANSFORMERS);
                addDocument.mutate({
                    workspaceId,
                    deskId,
                    document: { content: markdown, contentType: 'markdown' },
                });
            });
        }, 1500);
    }, [workspaceId, deskId, addDocument]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (saveTimeoutRef.current) {
                clearTimeout(saveTimeoutRef.current);
            }
        };
    }, []);

    // Load desk data
    const deskQuery = useDesk(workspaceId, deskId);
    const deskContent = React.useMemo(() => {
        const data = deskQuery.data as any;
        const content = data?.documents?.document?.content;
        return typeof content === 'string' ? content : undefined;
    }, [deskQuery.data]);

    const messages = React.useMemo(() => {
        const data = deskQuery.data as any;
        return (data?.messages || []) as Message[];
    }, [deskQuery.data]);

    return (
        <div className="h-screen flex flex-col bg-background">
            <LexicalComposer initialConfig={initialConfig}>
                <ToolbarPlugin openExportDialog={() => setIsExportDialogOpen(true)} />

                <div className="flex-1 overflow-auto bg-gray-100 dark:bg-gray-800 p-8">
                    <div className="bg-card border rounded-lg shadow-lg w-[8.5in] min-h-[11in] mx-auto mb-8">
                        <div className="relative p-[1in]">
                            {deskContent && <LoadContentPlugin content={deskContent} deskId={deskId} messages={messages} />}
                            <RichTextPlugin
                                contentEditable={
                                    <ContentEditable
                                        className="min-h-[9in] focus:outline-none"
                                        style={{ caretColor: 'hsl(var(--foreground))' }}
                                    />
                                }
                                placeholder={
                                    <div className="absolute top-[1in] left-[1in] text-muted-foreground/60 pointer-events-none select-none text-lg">
                                        Start writing...
                                    </div>
                                }
                                ErrorBoundary={() => (
                                    <div className="text-destructive p-4 bg-destructive/10 rounded-md border border-destructive/20">
                                        Some error occurred in the editor.
                                    </div>
                                )}
                            />
                        </div>
                    </div>
                </div>

                <HistoryPlugin />
                <AutoFocusPlugin />
                <ListPlugin />
                <LinkPlugin />
                <MarkdownShortcutPlugin transformers={TRANSFORMERS} />
                <OnChangePlugin onChange={onChange} />

                {isExportDialogOpen && (
                    <ExportDialog onClose={() => setIsExportDialogOpen(false)} />
                )}
            </LexicalComposer>
        </div>
    );
}